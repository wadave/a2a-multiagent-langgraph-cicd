# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A Gradio-based web interface for interacting with a remote A2A agent.

This application provides a chat interface that allows users to send queries to
a hosting agent running on Vertex AI. It handles authentication with Google
Cloud, creates an A2A (Agent-to-Agent) client, and streams responses back to the
user interface.

The main components are:
- A `GoogleAuth` class for handling `httpx` authentication.
- A `get_response_from_agent` function that encapsulates the logic for sending
  a message to the agent and processing its response.
- A `main` function that sets up and launches the Gradio application.
"""

import asyncio
import logging
import os
import traceback
from typing import AsyncIterator, List

import gradio as gr
import httpx
import vertexai
from a2a.client import Client, ClientConfig, ClientFactory
from a2a.types import (
    Message,
    Part,
    Role,
    TaskState,
    TextPart,
    TransportProtocol,
)
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest
from google.genai import types as genai_types  # Aliased to avoid conflict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


# Initialize Vertex AI session
vertexai.init(project=PROJECT_ID, location=LOCATION)

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=genai_types.HttpOptions(
        api_version="v1beta1", base_url=f"https://{LOCATION}-aiplatform.googleapis.com/"
    ),
)


# AGENT_ENGINE_ID is now the full resource name (projects/.../reasoningEngines/...)
# If it starts with "projects/", use it directly; otherwise construct it (backwards compatibility)
if AGENT_ENGINE_ID and AGENT_ENGINE_ID.startswith("projects/"):
    remote_a2a_agent_resource_name = AGENT_ENGINE_ID
else:
    # Fallback for old-style ID-only format
    remote_a2a_agent_resource_name = f"projects/{PROJECT_NUMBER}/locations/us-central1/reasoningEngines/{AGENT_ENGINE_ID}"


class GoogleAuth(httpx.Auth):
    """A custom httpx Auth class for Google Cloud authentication."""

    def __init__(self):
        """Initializes the GoogleAuth instance.

        This method retrieves the default Google Cloud credentials and project ID,
        and sets up an authentication request object for refreshing credentials.
        """
        self.credentials, self.project = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.auth_request = AuthRequest()

    def auth_flow(self, request):
        """Handles the authentication flow for an httpx request.

        This generator function refreshes the Google Cloud credentials if they have
        expired, adds the necessary `Authorization` header to the request, and
        then yields the request to be sent.

        Args:
            request: The `httpx` request object to be authenticated.
        """
        # Refresh the credentials if they are expired
        if not self.credentials.valid:
            logger.info("Credentials expired, refreshing...")
            self.credentials.refresh(self.auth_request)

        # Add the Authorization header to the request
        request.headers["Authorization"] = f"Bearer {self.credentials.token}"
        yield request


async def get_agent_card(resource_name: str):
    """Fetches the agent card from Vertex AI."""
    config = {
        "http_options": {
            "base_url": f"https://{LOCATION}-aiplatform.googleapis.com",
            "api_version": "v1beta1",
        }
    }

    remote_a2a_agent = client.agent_engines.get(
        name=resource_name,
        config=config,
    )

    return await remote_a2a_agent.handle_authenticated_agent_card()


async def get_response_from_agent(
    query: str,
    history: List[gr.ChatMessage],
) -> AsyncIterator[gr.ChatMessage]:
    """Get response from host agent."""

    a2a_client: Client = None  # Define client for the finally block
    httpx_client: httpx.AsyncClient = None  # Define httpx_client for the finally block

    try:
        # --- 1. Get Agent Card ---
        logger.info("Fetching agent card...")
        remote_a2a_agent_card = await get_agent_card(remote_a2a_agent_resource_name)
        logger.info("Agent card fetched.")

        # --- 2. Create HTTP Client with Auth ---
        httpx_client = httpx.AsyncClient(
            timeout=120,
            auth=GoogleAuth(),
        )

        # --- 3. Create A2A Client ---
        factory = ClientFactory(
            ClientConfig(
                supported_transports=[TransportProtocol.http_json],
                use_client_preference=True,
                httpx_client=httpx_client,  # Pass the authenticated client
            )
        )
        a2a_client = factory.create(remote_a2a_agent_card)
        logger.info("A2A client created.")

        # --- 4. Create Message ---
        message = Message(
            message_id=f"message-{os.urandom(8).hex()}",
            role=Role.user,
            parts=[Part(root=TextPart(text=query))],  # Simplified: just pass the query
        )

        # --- 5. Send Message and Stream Response ---
        logger.info(f"Sending message to agent: {query}")
        response_stream = a2a_client.send_message(message)

        final_result_text = None

        # Iterate over the async generator which yields task status updates
        async for response_chunk in response_stream:
            task_object = response_chunk[0]  # Task object is the first element

            logger.info(f"Received task update. Status: {task_object.status.state}")

            # Wait for the task to complete
            if task_object.status.state == TaskState.completed:
                logger.info("Task completed. Checking for artifacts...")
                if hasattr(task_object, "artifacts") and task_object.artifacts:
                    for artifact in task_object.artifacts:
                        # Find the first text part in the artifacts
                        if artifact.parts:
                            part = artifact.parts[0]

                            # Debug: print the actual type and value
                            logger.debug(f"DEBUG: part.root type: {type(part.root)}")
                            logger.debug(f"DEBUG: part.root value: {str(part.root)[:200]}...")

                            # Try to access as TextPart
                            if isinstance(part.root, TextPart):
                                final_result_text = part.root.text
                                logger.info(f"Found artifact text: {final_result_text[:50]}...")
                                break
                            # Handle list/dict responses (e.g., from LangGraph agents)
                            elif hasattr(part.root, 'text'):
                                final_result_text = part.root.text
                                logger.info(f"Found text field: {final_result_text[:50]}...")
                                break
                            # Try to parse as dict/list if it's serialized
                            else:
                                try:
                                    import ast
                                    import json
                                    import re

                                    # Convert to string
                                    part_str = str(part.root)

                                    # Check if it has "signature:" prefix and extract the list
                                    if 'signature:' in part_str:
                                        # Extract the part after "signature:"
                                        match = re.search(r'signature:\s*(\[.*\])', part_str)
                                        if match:
                                            list_str = match.group(1)
                                            parsed = ast.literal_eval(list_str)
                                            if isinstance(parsed, list) and len(parsed) > 0:
                                                if isinstance(parsed[0], dict) and 'text' in parsed[0]:
                                                    final_result_text = parsed[0]['text']
                                                    logger.info(f"Extracted text from signature list: {final_result_text[:50]}...")
                                                    break
                                    # If it looks like a list representation
                                    elif part_str.startswith('[') and 'text' in part_str:
                                        parsed = ast.literal_eval(part_str)
                                        if isinstance(parsed, list) and len(parsed) > 0:
                                            if isinstance(parsed[0], dict) and 'text' in parsed[0]:
                                                final_result_text = parsed[0]['text']
                                                logger.info(f"Extracted text from list: {final_result_text[:50]}...")
                                                break
                                except Exception as e:
                                    logger.debug(f"DEBUG: Failed to parse - {e}")
                                    pass
                if final_result_text:
                    break  # Stop iterating task updates

            # Handle task failure
            elif task_object.status.state == TaskState.failed:
                error_message = f"Task failed: {task_object.status.message if task_object.status else 'Unknown error'}"
                logger.error(error_message)
                yield gr.ChatMessage(role="assistant", content=error_message)
                return  # Exit the generator

        # --- 6. Yield Final Response ---
        if final_result_text:
            yield gr.ChatMessage(role="assistant", content=final_result_text)
        else:
            logger.info("Task finished but no text artifact was found.")
            yield gr.ChatMessage(
                role="assistant",
                content="I processed your request but found no text response.",
            )

    except Exception as e:
        logger.error(f"Error in get_response_from_agent (Type: {type(e)}): {e}", exc_info=True)
        yield gr.ChatMessage(
            role="assistant",
            content=f"An error occurred: {e}",
        )
    finally:
        # --- 7. Clean up clients ---
        # Close the A2A client, which also closes the httpx_client it manages
        if a2a_client:
            await a2a_client.close()
            logger.info("A2A client closed.")
        elif httpx_client:
            # Fallback if a2a_client creation failed but httpx_client was made
            await httpx_client.aclose()
            logger.info("HTTPX client closed.")


async def main():
    """Main gradio app."""

    with gr.Blocks(theme=gr.themes.Ocean(), title="A2A Host Agent") as demo:
        # Using gr.Markdown to center the image and title
        with gr.Row():
            gr.Image(
                "static/a2a.png",
                width=100,
                height=100,
                scale=0,
                show_label=False,
                container=False,
                elem_classes=["centered-image"],  # Requires custom CSS
            )

        gr.ChatInterface(
            get_response_from_agent,
            title="A2A Host Agent",
            description="This assistant can help you to check weather and find cocktail information",
        )

    logger.info("Launching Gradio interface on http://0.0.0.0:8080")
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=8080,
    )
    logger.info("Gradio application has been shut down.")


if __name__ == "__main__":
    # Create the 'static' directory if it doesn't exist for the image
    if not os.path.exists("static"):
        os.makedirs("static")
        logger.info("Created 'static' directory. Please add your 'a2a.png' image there.")

    asyncio.run(main())

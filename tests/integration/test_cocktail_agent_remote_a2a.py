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
# Author: Dave Wang

import asyncio
import logging
import os
import subprocess
from dotenv import load_dotenv

import httpx
import vertexai
from google.genai import types

from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    Message,
    Part,
    Role,
    TaskQueryParams,
    TextPart,
    TransportProtocol,
)

logging.basicConfig(level=logging.INFO)
load_dotenv()


def get_bearer_token():
    """Fetches a Google Cloud bearer token using Application Default Credentials."""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request

        credentials, project = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
        print(
            "Please ensure you have authenticated with 'gcloud auth application-default login'."
        )
    return None


async def test_remote_cocktail_agent():
    print("\n=== Testing Remote Cocktail Agent with A2A Client ===\n")

    # Configuration
    project_id = os.environ.get("PROJECT_ID", "dw-genai-dev")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER", "496235138247")
    cocktail_agent_id = "271714611990888448"

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1", base_url=f"https://{location}-aiplatform.googleapis.com/"
        ),
    )

    # Get the remote agent
    print("Getting remote agent...")
    agent_resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{cocktail_agent_id}"
    config = {"http_options": {"base_url": f"https://{location}-aiplatform.googleapis.com", "api_version": "v1beta1"}}
    remote_agent = client.agent_engines.get(name=agent_resource_name, config=config)

    # Get agent card
    print("Fetching agent card...")
    agent_card = await remote_agent.handle_authenticated_agent_card()
    print(f"Agent: {agent_card.name}")
    print(f"URL: {agent_card.url}")
    print(f"Skills: {[s.description for s in agent_card.skills]}\n")

    # Set up A2A client
    bearer_token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    factory = ClientFactory(
        ClientConfig(
            supported_transports=[TransportProtocol.http_json],
            use_client_preference=True,
            httpx_client=httpx.AsyncClient(
                timeout=120,
                headers=headers,
            ),
        )
    )

    a2a_client = factory.create(agent_card)

    # Test query
    query = "What are the ingredients for a Margarita?"
    print(f"Sending query: {query}")

    message = Message(
        message_id=f"message-{os.urandom(8).hex()}",
        role=Role.user,
        parts=[Part(root=TextPart(text=query))],
    )

    response = a2a_client.send_message(message)

    async for response_chunk in response:
        task_object = response_chunk[0]
        task_id = task_object.id

    print(f"Task started: {task_id}")
    print(f"Status: {task_object.status.state}")

    # Poll for result
    print("\nPolling for result...")
    for i in range(30):  # Poll up to 30 times
        await asyncio.sleep(2)

        task_data = {
            "id": task_id,
            "historyLength": 1,
        }
        response = await a2a_client.get_task(TaskQueryParams(**task_data))

        print(f"Poll {i+1}: {response.status.state}")

        if response.status.state == "TASK_STATE_COMPLETED":
            if hasattr(response, "artifacts") and response.artifacts:
                print("\n=== Answer ===")
                for artifact in response.artifacts:
                    result_text = artifact.parts[0].root.text
                    print(result_text)
                print("=============\n")
                return True
            break
        elif response.status.state == "TASK_STATE_FAILED":
            print(f"\nTask failed: {response.status.message}")
            return False

    print("\nTest timed out")
    return False


if __name__ == "__main__":
    success = asyncio.run(test_remote_cocktail_agent())
    exit(0 if success else 1)

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
import json
from dotenv import load_dotenv

import vertexai
from google.genai import types

logging.basicConfig(level=logging.INFO)
load_dotenv()


async def test_remote_cocktail_agent():
    print("\n=== Testing Remote Cocktail Agent ===\n")

    # Configuration
    project_id = os.environ.get("PROJECT_ID", "dw-genai-dev")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER", "496235138247")
    # cocktail_agent_id = "271714611990888448"  # Old ID
    cocktail_agent_id = "186286956559204352"  # Cocktail Agent lg - LangGraph

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
    print(f"Getting remote agent (ID: {cocktail_agent_id})...")
    agent_resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{cocktail_agent_id}"

    config = {"http_options": {"base_url": f"https://{location}-aiplatform.googleapis.com", "api_version": "v1beta1"}}
    remote_agent = client.agent_engines.get(name=agent_resource_name, config=config)

    # Get agent card
    print("Fetching agent card...")
    agent_card = await remote_agent.handle_authenticated_agent_card()
    print(f"Agent: {agent_card.name}")
    print(f"URL: {agent_card.url}")
    print(f"Skills: {[s.description for s in agent_card.skills]}\n")

    # Test query
    query = "What are the ingredients for a Margarita?"
    print(f"Sending query: {query}\n")

    try:
        # Send message and get task
        message_data = {
            "message": {
                "messageId": f"msg-{os.urandom(8).hex()}",
                "content": [{"text": query}],
                "role": "ROLE_USER",
            },
        }

        # Create a mock request (similar to local test)
        from starlette.requests import Request

        def receive_wrapper(data: dict):
            async def receive():
                byte_data = json.dumps(data).encode("utf-8")
                return {"type": "http.request", "body": byte_data, "more_body": False}
            return receive

        scope = {
            "type": "http",
            "http_version": "1.1",
            "headers": [(b"content-type", b"application/json")],
            "app": None,
        }
        receiver = receive_wrapper(message_data)
        request = Request(scope, receiver)

        response = await remote_agent.on_message_send(request=request, context=None)
        task_id = response["task"]["id"]
        print(f"Task started: {task_id}")
        print(f"Initial status: {response['task']['status']['state']}")

        # Poll for result
        print("\nPolling for result...")
        for i in range(30):
            await asyncio.sleep(3)

            task_data = {"id": task_id}
            scope = {
                "type": "http",
                "http_version": "1.1",
                "query_string": b"",
                "app": None,
                "path_params": task_data,
            }

            async def receive():
                return {"type": "http.disconnect"}

            request = Request(scope, receive)
            response2 = await remote_agent.on_get_task(request=request, context=None)

            status = response2["status"]["state"]
            print(f"Poll {i+1}: {status}")

            if status == "TASK_STATE_COMPLETED":
                print("\n=== Answer ===")
                for artifact in response2.get("artifacts", []):
                    if artifact.get("parts"):
                        print(artifact["parts"][0]["text"])
                print("=============\n")
                return True
            elif status == "TASK_STATE_FAILED":
                print(f"\nTask failed: {response2['status'].get('message')}")
                return False

        print("\nTest timed out")
        return False

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_remote_cocktail_agent())
    exit(0 if success else 1)

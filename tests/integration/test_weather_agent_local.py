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

import os
import sys
import json
import logging
import asyncio
from typing import Any, Callable, Awaitable
from starlette.requests import Request
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from a2a_agents.weather_agent.weather_agent_card import weather_agent_card
from a2a_agents.weather_agent.agent_executor import WeatherAgentExecutor
from vertexai.preview.reasoning_engines import A2aAgent

# Helpers from notebook
def receive_wrapper(data: dict) -> Callable[[], Awaitable[dict]]:
    """Creates a mock ASGI receive callable for testing."""
    async def receive():
        byte_data = json.dumps(data).encode("utf-8")
        return {"type": "http.request", "body": byte_data, "more_body": False}
    return receive

def build_post_request(
    data: dict[str, Any] | None = None, path_params: dict[str, str] | None = None
) -> Request:
    """Builds a mock Starlette Request object for a POST request with JSON data."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "headers": [(b"content-type", b"application/json")],
        "app": None,
    }
    if path_params:
        scope["path_params"] = path_params
    receiver = receive_wrapper(data)
    return Request(scope, receiver)

def build_get_request(path_params: dict[str, str] | None = None) -> Request:
    """Builds a mock Starlette Request object for a GET request."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "query_string": b"",
        "app": None,
    }
    if path_params:
        scope["path_params"] = path_params

    async def receive():
        return {"type": "http.disconnect"}

    return Request(scope, receive)

async def test_weather_agent_local():
    print("--- Testing Weather Agent Locally ---")
    load_dotenv()

    # Ensure environment variables are set
    if not os.environ.get("PROJECT_ID"):
        print("Error: PROJECT_ID not set")
        return

    # Force LOCATION to us-central1 as required by the error message
    os.environ["LOCATION"] = "us-central1"
    os.environ["GOOGLE_CLOUD_REGION"] = "us-central1"

    if not os.environ.get("WEA_MCP_SERVER_URL"):
        # Default to the deployed LangGraph MCP server URL
        os.environ["WEA_MCP_SERVER_URL"] = "https://weather-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp/"
        print(f"Set WEA_MCP_SERVER_URL to {os.environ['WEA_MCP_SERVER_URL']}")

    # Initialize Vertex AI
    import vertexai
    vertexai.init(project=os.environ.get("PROJECT_ID"), location="us-central1")

    # 1. Initialize Agent
    print("Initializing A2aAgent...")

    a2a_agent = A2aAgent(
        agent_card=weather_agent_card,
        agent_executor_builder=WeatherAgentExecutor,
    )
    a2a_agent.set_up()
    print("Agent set up.")

    # 2. Get Agent Card
    print("Fetching agent card...")
    request = build_get_request(None)
    response = await a2a_agent.handle_authenticated_agent_card(
        request=request, context=None
    )
    if isinstance(response, dict):
        print(f"Agent Name: {response.get('name', 'N/A')}")
        print(f"Skills: {len(response.get('skills', []))}")
    else:
        print(f"Agent Name: {response.name}")
        print(f"Skills: {len(response.skills)}")

    # 3. Send Message
    print("Sending message: 'What is the weather forecast for New York, NY?'")
    message_data = {
        "message": {
            "messageId": f"msg-{os.urandom(8).hex()}",
            "content": [{"text": "What is the weather forecast for New York, NY?"}],
            "role": "ROLE_USER",
        },
    }
    request = build_post_request(message_data)
    response = await a2a_agent.on_message_send(request=request, context=None)

    task_id = response["task"]["id"]
    print(f"Task started: {task_id}")

    # 4. Poll for Result
    print("Polling for result...")
    max_retries = 30
    for i in range(max_retries):
        task_data = {"id": task_id}
        request = build_get_request(task_data)
        response2 = await a2a_agent.on_get_task(request=request, context=None)

        status = response2["status"]["state"]
        print(f"Poll {i+1}: {status}")

        if status == "TASK_STATE_COMPLETED":
            for artifact in response2.get("artifacts", []):
                if artifact.get("parts"):
                    print(f"Answer: {artifact['parts'][0]['text'][:200]}...")
            break
        elif status == "TASK_STATE_FAILED":
            print(f"Task failed: {response2['status'].get('message')}")
            break

        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_weather_agent_local())

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
import json
import logging
import os
import subprocess
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.requests import Request
from vertexai.preview.reasoning_engines import A2aAgent

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import a2a_agents.common.adk_base_mcp_agent_executor as executor_module

from a2a_agents.cocktail_agent.agent_executor import CocktailAgentExecutor
from a2a_agents.cocktail_agent.cocktail_agent_card import cocktail_agent_card

logging.basicConfig(level=logging.INFO)

# --- Monkeypatch for Local Auth ---


def mock_get_gcp_auth_headers(audience: str) -> dict[str, str]:
    """Mock that uses gcloud to get a token working for local user."""
    try:
        # Use audiences flag for OIDC token
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token", f"--audiences={audience}"], text=True
        ).strip()
        return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        # Fallback to no-audience if that fails (some accounts don't support it)
        try:
            token = subprocess.check_output(
                ["gcloud", "auth", "print-identity-token"], text=True
            ).strip()
            return {"Authorization": f"Bearer {token}"}
        except:
            logging.error(f"Failed to get gcloud token: {e}")
            return {}


# Apply the patch
executor_module.get_gcp_auth_headers = mock_get_gcp_auth_headers
logging.info("Monkeypatched get_gcp_auth_headers for local testing")

# --- Helpers from Notebook ---


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


def build_get_request(path_params: dict[str, str]) -> Request:
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


# --- Test Logic ---


async def test_agent_locally():
    print("\n--- Initializing A2aAgent ---")

    # Ensure environment variables are set for AdkBaseMcpAgentExecutor
    os.environ["PROJECT_ID"] = os.environ.get("PROJECT_ID", "dw-genai-dev")
    os.environ["LOCATION"] = "us-central1"
    os.environ["CT_MCP_SERVER_URL"] = (
        "https://cocktail-remote-mcp-server-496235138247.us-central1.run.app/mcp/sse"
    )

    a2a_agent = A2aAgent(
        agent_card=cocktail_agent_card, agent_executor_builder=CocktailAgentExecutor
    )
    # The set_up() call triggers the creation of the Agent Engine if agent_engine_id is None
    # We want to skip that for local tests if possible, but AdkBaseMcpAgentExecutor.__init__ calls it.
    a2a_agent.set_up()

    print("\n--- Getting Agent Card ---")
    request = build_get_request(None)
    response = await a2a_agent.handle_authenticated_agent_card(request=request, context=None)
    # response is an AgentCard object if successful
    print(f"Agent Name: {getattr(response, 'name', 'Unknown')}")

    print("\n--- Sending Message ---")
    message_data = {
        "message": {
            "messageId": f"msg-{os.urandom(8).hex()}",
            "content": [{"text": "ingredients for a Margarita?"}],
            "role": "ROLE_USER",
        },
    }
    request = build_post_request(message_data)
    response = await a2a_agent.on_message_send(request=request, context=None)

    task_id = response["task"]["id"]
    print(f"Task ID: {task_id}")

    print("\n--- Polling for Result ---")
    task_data = {"id": task_id}

    # Simple poll loop
    for i in range(15):  # Try 15 times
        request = build_get_request(task_data)
        response = await a2a_agent.on_get_task(request=request, context=None)
        state = response.get("status", {}).get("state")
        print(f"Poll {i + 1} - Task State: {state}")

        if state == "TASK_STATE_COMPLETED":
            for artifact in response.get("artifacts", []):
                if artifact["parts"] and "text" in artifact["parts"][0]:
                    print(f"\nAnswer:\n{artifact['parts'][0]['text']}")
            break
        elif state == "TASK_STATE_FAILED":
            print(f"Task Failed: {response.get('status', {}).get('message')}")
            break

        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(test_agent_locally())

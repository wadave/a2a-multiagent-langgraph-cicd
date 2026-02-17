#!/usr/bin/env python
"""Simple test for remotely deployed hosting agent."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

import vertexai
from google.genai import types
from a2a.types import Message, Part, Role, TextPart, TransportProtocol
from a2a.client import ClientFactory, ClientConfig
import httpx

load_dotenv()

async def test_hosting_agent():
    print("\n" + "="*60)
    print("Testing Hosting Agent (Remote Deployment)")
    print("="*60)

    project_id = os.environ.get("PROJECT_ID", "dw-genai-dev")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER", "496235138247")
    hosting_agent_id = os.environ.get("AGENT_ENGINE_ID", "4971924510593777664")

    print(f"\nProject: {project_id}")
    print(f"Location: {location}")
    print(f"Hosting Agent ID: {hosting_agent_id}")

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
            base_url=f"https://{location}-aiplatform.googleapis.com/"
        ),
    )

    # Get the hosting agent
    print("\n1. Fetching hosting agent...")
    agent_resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{hosting_agent_id}"
    config = {
        "http_options": {
            "base_url": f"https://{location}-aiplatform.googleapis.com",
            "api_version": "v1beta1"
        }
    }

    remote_agent = client.agent_engines.get(name=agent_resource_name, config=config)

    # Get agent card
    print("2. Fetching agent card...")
    agent_card = await remote_agent.handle_authenticated_agent_card()
    print(f"   ✓ Agent Name: {agent_card.name}")
    print(f"   ✓ URL: {agent_card.url}")
    print(f"   ✓ Skills: {[s.description for s in agent_card.skills]}")

    # Get authentication token
    from google.auth import default
    from google.auth.transport.requests import Request

    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = Request()
    credentials.refresh(request)
    bearer_token = credentials.token

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    # Create A2A client
    factory = ClientFactory(
        ClientConfig(
            supported_transports=[TransportProtocol.http_json],
            use_client_preference=True,
            httpx_client=httpx.AsyncClient(timeout=120, headers=headers),
        )
    )

    a2a_client = factory.create(agent_card)

    # Test 1: Simple greeting
    print("\n" + "="*60)
    print("Test 1: Simple greeting (should respond without tools)")
    print("="*60)

    query = "Hello!"
    print(f"Query: {query}")

    message = Message(
        message_id=f"msg-{os.urandom(8).hex()}",
        role=Role.user,
        parts=[Part(root=TextPart(text=query))],
    )

    response_stream = a2a_client.send_message(message)

    async for response_chunk in response_stream:
        task_object = response_chunk[0]

    print(f"Task ID: {task_object.id}")
    print(f"Status: {task_object.status.state}")

    if hasattr(task_object, "artifacts") and task_object.artifacts:
        print("\n✓ Response received:")
        for artifact in task_object.artifacts:
            answer = artifact.parts[0].root.text
            print(f"  {answer}\n")
    else:
        print("✗ No artifacts in response")
        return False

    # Test 2: Cocktail question
    print("="*60)
    print("Test 2: Cocktail question (should use Cocktail Agent)")
    print("="*60)

    query = "What are the ingredients in a Margarita?"
    print(f"Query: {query}")

    message = Message(
        message_id=f"msg-{os.urandom(8).hex()}",
        role=Role.user,
        parts=[Part(root=TextPart(text=query))],
    )

    response_stream = a2a_client.send_message(message)

    async for response_chunk in response_stream:
        task_object = response_chunk[0]

    print(f"Task ID: {task_object.id}")
    print(f"Status: {task_object.status.state}")

    # If not completed, poll for result
    if task_object.status.state != "TASK_STATE_COMPLETED":
        print("\nPolling for completion...")
        for i in range(30):
            await asyncio.sleep(2)
            try:
                from a2a.types import TaskQueryParams
                task_data = {"id": task_object.id, "historyLength": 0}
                response = await a2a_client.get_task(TaskQueryParams(**task_data))
                print(f"  Poll {i+1}: {response.status.state}")

                if response.status.state == "TASK_STATE_COMPLETED":
                    task_object = response
                    break
                elif response.status.state == "TASK_STATE_FAILED":
                    print(f"✗ Task failed: {response.status.message}")
                    return False
            except Exception as e:
                print(f"  Poll {i+1} error: {e}")
                continue

    if hasattr(task_object, "artifacts") and task_object.artifacts:
        print("\n✓ Response received:")
        for artifact in task_object.artifacts:
            answer = artifact.parts[0].root.text
            print(f"  {answer[:300]}...\n")

            # Check if response mentions margarita ingredients
            answer_lower = answer.lower()
            if "tequila" in answer_lower or "lime" in answer_lower or "margarita" in answer_lower:
                print("✓ Response contains cocktail information!")
            else:
                print("⚠ Response might not have correct cocktail info")
    else:
        print("✗ No artifacts in response")
        return False

    # Test 3: Weather question
    print("="*60)
    print("Test 3: Weather question (should use Weather Agent)")
    print("="*60)

    query = "What's the weather in San Francisco?"
    print(f"Query: {query}")

    message = Message(
        message_id=f"msg-{os.urandom(8).hex()}",
        role=Role.user,
        parts=[Part(root=TextPart(text=query))],
    )

    response_stream = a2a_client.send_message(message)

    async for response_chunk in response_stream:
        task_object = response_chunk[0]

    print(f"Task ID: {task_object.id}")
    print(f"Status: {task_object.status.state}")

    # If not completed, poll for result
    if task_object.status.state != "TASK_STATE_COMPLETED":
        print("\nPolling for completion...")
        for i in range(30):
            await asyncio.sleep(2)
            try:
                from a2a.types import TaskQueryParams
                task_data = {"id": task_object.id, "historyLength": 0}
                response = await a2a_client.get_task(TaskQueryParams(**task_data))
                print(f"  Poll {i+1}: {response.status.state}")

                if response.status.state == "TASK_STATE_COMPLETED":
                    task_object = response
                    break
                elif response.status.state == "TASK_STATE_FAILED":
                    print(f"✗ Task failed: {response.status.message}")
                    return False
            except Exception as e:
                print(f"  Poll {i+1} error: {e}")
                continue

    if hasattr(task_object, "artifacts") and task_object.artifacts:
        print("\n✓ Response received:")
        for artifact in task_object.artifacts:
            answer = artifact.parts[0].root.text
            print(f"  {answer[:300]}...\n")

            # Check if response mentions weather
            answer_lower = answer.lower()
            if "weather" in answer_lower or "forecast" in answer_lower or "temperature" in answer_lower:
                print("✓ Response contains weather information!")
            else:
                print("⚠ Response might not have correct weather info")
    else:
        print("✗ No artifacts in response")
        return False

    print("="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_hosting_agent())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Test all deployed agents to see which ones support A2A protocol."""

import os
import asyncio
import vertexai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "dw-genai-dev")
project_number = os.environ.get("PROJECT_NUMBER", "496235138247")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

print(f"Project: {project_id} ({project_number})")
print(f"Location: {location}\n")

vertexai.init(project=project_id, location=location)

client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(
        api_version="v1beta1", base_url=f"https://{location}-aiplatform.googleapis.com/"
    ),
)

agents_to_test = [
    ("9013342226205376512", "Hosting Agent GE2 Staging"),
    ("5018649356727746560", "Hosting Agent lg - LangGraph"),
    ("247367026505416704", "Hosting Agent adk-mb - ADK"),
]

async def test_agent(agent_id, agent_name):
    print(f"\n{'='*60}")
    print(f"Testing: {agent_name}")
    print(f"ID: {agent_id}")
    print('='*60)

    try:
        # Get agent
        agent_resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{agent_id}"
        config = {
            "http_options": {
                "base_url": f"https://{location}-aiplatform.googleapis.com",
                "api_version": "v1beta1"
            }
        }

        remote_agent = client.agent_engines.get(name=agent_resource_name, config=config)
        print(f"✓ Agent found")

        # Try to get agent card (A2A protocol)
        try:
            if hasattr(remote_agent, 'handle_authenticated_agent_card'):
                agent_card = await remote_agent.handle_authenticated_agent_card()
                print(f"✓ A2A Protocol supported")
                print(f"  Agent Name: {agent_card.name}")
                print(f"  URL: {agent_card.url}")
                print(f"  Skills: {[s.description for s in agent_card.skills]}")
                return True
            else:
                print(f"✗ A2A Protocol NOT supported (no handle_authenticated_agent_card method)")
                return False
        except Exception as e:
            print(f"✗ A2A Protocol check failed: {e}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main():
    results = {}
    for agent_id, agent_name in agents_to_test:
        result = await test_agent(agent_id, agent_name)
        results[agent_name] = result

    print(f"\n{'='*60}")
    print("Summary:")
    print('='*60)
    for agent_name, supports_a2a in results.items():
        status = "✓ Supports A2A" if supports_a2a else "✗ No A2A support"
        print(f"{agent_name}: {status}")

if __name__ == "__main__":
    asyncio.run(main())

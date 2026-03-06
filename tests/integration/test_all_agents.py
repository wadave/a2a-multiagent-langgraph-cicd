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
#!/usr/bin/env python3
"""Test all deployed agents to see which ones support A2A protocol."""

import asyncio
import os

import vertexai
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
project_number = os.environ.get("PROJECT_NUMBER")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if not project_id or not project_number:
    raise ValueError("GOOGLE_CLOUD_PROJECT and PROJECT_NUMBER must be set")

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

# Define via environment variables or CLI since these change often
HOSTING_AGENT_IDS = os.environ.get("HOSTING_AGENT_IDS", "").split(",")

# Fallback strictly for local debugging if desired, but ideally environment driven
agents_to_test = [
    (agent_id.strip(), f"Agent {agent_id.strip()}")
    for agent_id in HOSTING_AGENT_IDS
    if agent_id.strip()
]

if not agents_to_test:
    print("Warning: No agents configured to test. Set HOSTING_AGENT_IDS environment variable.")


async def test_agent(agent_id, agent_name):
    print(f"\n{'=' * 60}")
    print(f"Testing: {agent_name}")
    print(f"ID: {agent_id}")
    print("=" * 60)

    try:
        # Get agent
        agent_resource_name = (
            f"projects/{project_number}/locations/{location}/reasoningEngines/{agent_id}"
        )
        config = {
            "http_options": {
                "base_url": f"https://{location}-aiplatform.googleapis.com",
                "api_version": "v1beta1",
            }
        }

        remote_agent = client.agent_engines.get(name=agent_resource_name, config=config)
        print("✓ Agent found")

        # Try to get agent card (A2A protocol)
        try:
            if hasattr(remote_agent, "handle_authenticated_agent_card"):
                agent_card = await remote_agent.handle_authenticated_agent_card()
                print("✓ A2A Protocol supported")
                print(f"  Agent Name: {agent_card.name}")
                print(f"  URL: {agent_card.url}")
                print(f"  Skills: {[s.description for s in agent_card.skills]}")
                return True
            else:
                print("✗ A2A Protocol NOT supported (no handle_authenticated_agent_card method)")
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

    print(f"\n{'=' * 60}")
    print("Summary:")
    print("=" * 60)
    for agent_name, supports_a2a in results.items():
        status = "✓ Supports A2A" if supports_a2a else "✗ No A2A support"
        print(f"{agent_name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())

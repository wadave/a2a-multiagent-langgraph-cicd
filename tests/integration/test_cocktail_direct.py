#!/usr/bin/env python3
"""Test cocktail agent directly with A2A protocol."""

import asyncio
import os
from dotenv import load_dotenv
import vertexai
from google.genai import types
from a2a.types import Message, Part, TextPart, Role

load_dotenv()

async def test_cocktail_direct():
    project_id = os.environ.get("PROJECT_ID", "dw-genai-dev")
    project_number = os.environ.get("PROJECT_NUMBER", "496235138247")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    cocktail_agent_id = "4584614942639915008"

    print(f"\n=== Testing Cocktail Agent Directly ===")
    print(f"Agent ID: {cocktail_agent_id}\n")

    vertexai.init(project=project_id, location=location)

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
            base_url=f"https://{location}-aiplatform.googleapis.com/"
        ),
    )

    # Get agent
    agent_resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{cocktail_agent_id}"
    config = {
        "http_options": {
            "base_url": f"https://{location}-aiplatform.googleapis.com",
            "api_version": "v1beta1"
        }
    }

    try:
        agent = client.agent_engines.get(name=agent_resource_name, config=config)
        print(f"✓ Agent retrieved successfully")

        # Try to get card
        card = await agent.handle_authenticated_agent_card()
        print(f"✓ Agent card: {card.name}")
        print(f"  Skills: {[s.description for s in card.skills]}")

        # Try simple query method (not A2A)
        print(f"\nTrying query() method...")
        try:
            result = agent.query(input="What is in a margarita?")
            print(f"✓ Query worked: {result}")
            return True
        except Exception as e:
            print(f"✗ Query failed: {e}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_cocktail_direct())

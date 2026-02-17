#!/usr/bin/env python3
"""List all deployed reasoning engines (agents) in Vertex AI."""

import os
import vertexai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "dw-genai-dev")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

print(f"Project: {project_id}")
print(f"Location: {location}\n")

vertexai.init(project=project_id, location=location)

client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(
        api_version="v1beta1", base_url=f"https://{location}-aiplatform.googleapis.com/"
    ),
)

print("Listing all reasoning engines (agents)...")
try:
    agents = list(client.agent_engines.list())

    if not agents:
        print("No agents found.")
    else:
        print(f"Found {len(agents)} agent(s):\n")
        for i, agent in enumerate(agents, 1):
            api_resource = agent.api_resource
            resource_name = api_resource.name
            agent_id = resource_name.split('/')[-1]
            display_name = api_resource.display_name if hasattr(api_resource, 'display_name') else 'N/A'
            description = api_resource.description if hasattr(api_resource, 'description') else 'N/A'
            create_time = api_resource.create_time if hasattr(api_resource, 'create_time') else 'N/A'

            print(f"{i}. {display_name}")
            print(f"   ID: {agent_id}")
            print(f"   Full Name: {resource_name}")
            print(f"   Description: {description}")
            print(f"   Created: {create_time}")

            # Check if it has -lg in the name
            if '-lg' in display_name.lower() or 'langgraph' in display_name.lower():
                print(f"   ** This is a LangGraph agent **")
            print()

except Exception as e:
    print(f"Error listing agents: {e}")
    import traceback
    traceback.print_exc()

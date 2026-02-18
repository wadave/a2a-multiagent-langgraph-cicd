import os
import vertexai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

project_id = os.environ.get("PROJECT_ID") or "dw-genai-dev"
location = os.environ.get("GOOGLE_CLOUD_REGION") or "us-central1"

# Agent IDs from deployment output
# Old IDs (not working):
# COCKTAIL_AGENT_ID = "271714611990888448"
# WEATHER_AGENT_ID = "8434488936599912448"

# LangGraph agents (current):
# LangGraph agents (current):
COCKTAIL_AGENT_ID = os.environ.get("COCKTAIL_AGENT_ID")
WEATHER_AGENT_ID = os.environ.get("WEATHER_AGENT_ID")

if not COCKTAIL_AGENT_ID or not WEATHER_AGENT_ID:
    raise ValueError("COCKTAIL_AGENT_ID and WEATHER_AGENT_ID environment variables are required")

vertexai.init(project=project_id, location=location)

client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(
        api_version="v1beta1", base_url=f"https://{location}-aiplatform.googleapis.com/"
    ),
)

def test_remote_agent(agent_id, agent_name, query):
    print(f"\n--- Testing {agent_name} ({agent_id}) ---")
    try:
        # Get project number for resource name
        project_number = os.environ.get("PROJECT_NUMBER")
        if not project_number:
            raise ValueError("PROJECT_NUMBER environment variable is required")
        agent_resource_name = f"projects/{project_number}/locations/{location}/reasoningEngines/{agent_id}"

        agent = client.agent_engines.get(name=agent_resource_name)
        print(f"Querying: {query}")
        # Reasoning Engine query method
        response = agent.query(input=query)
        print("Response received.")

        # Pretty print response
        if isinstance(response, dict):
            import json
            print(json.dumps(response, indent=2))
        else:
            print(response)

    except Exception as e:
        print(f"Error testing {agent_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    test_remote_agent(COCKTAIL_AGENT_ID, "Cocktail Agent", "What is in a margarita?")
    test_remote_agent(WEATHER_AGENT_ID, "Weather Agent", "What is the weather in New York, NY?")

if __name__ == "__main__":
    main()

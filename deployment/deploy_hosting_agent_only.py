#!/usr/bin/env python
"""Deploy only the hosting agent with updated code."""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path to import from deployment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import vertexai
from google.genai import Client

from a2a_agents.hosting_agent.hosting_agent_card import hosting_agent_card
from a2a_agents.hosting_agent.langgraph_orchestrator_agent_executor import HostingAgentExecutor

# Import the deploy_agent function from the main deployment script
sys.path.insert(0, os.path.dirname(__file__))
from deploy_agents import deploy_agent

load_dotenv()
logging.basicConfig(level=logging.INFO)

def main():
    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER")
    bucket_name = f"{project_id}-bucket"
    google_genai_model = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")

    # Change working directory to src
    os.chdir(os.path.join(os.path.dirname(__file__), "../src"))
    logging.info(f"Changed working directory to {os.getcwd()}")

    vertexai.init(project=project_id, location=location)
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options={"api_version": "v1beta1"},
    )

    # Use the already-deployed cocktail and weather agents from environment variables
    ct_agent_name = os.environ.get("CT_AGENT_NAME", f"projects/{project_number}/locations/{location}/reasoningEngines/2922892233256468480")
    wea_agent_name = os.environ.get("WEA_AGENT_NAME", f"projects/{project_number}/locations/{location}/reasoningEngines/3747050965065269248")

    # Build A2A URL endpoints
    ct_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{ct_agent_name}/a2a"
    wea_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{wea_agent_name}/a2a"

    logging.info(f"CT_AGENT_URL: {ct_agent_url}")
    logging.info(f"WEA_AGENT_URL: {wea_agent_url}")

    # Deploy Hosting Agent
    try:
        host_agent_name = deploy_agent(
            client,
            "Hosting lg Agent",
            hosting_agent_card,
            HostingAgentExecutor,
            project_id,
            project_number,
            location,
            bucket_name,
            {
                "WEA_AGENT_URL": wea_agent_url,
                "CT_AGENT_URL": ct_agent_url,
                "PROJECT_NUMBER": project_number,
                "GOOGLE_CLOUD_LOCATION": location,
                "GOOGLE_GENAI_MODEL": google_genai_model
            },
            ["a2a_agents"]
        )
        logging.info(f"Successfully deployed Hosting Agent: {host_agent_name}")
        agent_id = host_agent_name.split("/")[-1]
        logging.info(f"Agent ID: {agent_id}")
        print(f"\n\nAGENT_ENGINE_ID={agent_id}")
    except Exception as e:
        logging.error(f"Failed to deploy Hosting Agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

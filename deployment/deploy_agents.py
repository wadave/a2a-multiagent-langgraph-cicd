import os
import argparse
import logging
from dotenv import load_dotenv

import vertexai
from google.genai import types
from vertexai.preview.reasoning_engines import A2aAgent

from cocktail_agent.cocktail_agent_card import cocktail_agent_card
from cocktail_agent.agent_executor import CocktailAgentExecutor

from weather_agent.weather_agent_card import weather_agent_card
from weather_agent.agent_executor import WeatherAgentExecutor

from hosting_agent.hosting_agent_card import hosting_agent_card
from hosting_agent.langgraph_orchestrator_agent_executor import HostingAgentExecutor

logging.basicConfig(level=logging.INFO)

def deploy_agent(client, agent_name, agent_card, executor_builder, project_id, project_number, location, bucket_name, extra_env_vars, extra_packages):
    agent = A2aAgent(agent_card=agent_card, agent_executor_builder=executor_builder)
    
    env_vars = {
        "PROJECT_ID": project_id,
        "LOCATION": location,
        "BUCKET": bucket_name,
        "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
        "DEBUG_MODE": "False",
    }
    env_vars.update(extra_env_vars)
    
    logging.info(f"Deploying {agent_name} to Agent Engine...")
    
    remote_agent = client.agent_engines.create(
        agent=agent,
        config={
            "display_name": agent.agent_card.name,
            "description": agent.agent_card.description,
            "service_account": f"{project_number}-compute@developer.gserviceaccount.com",
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.112.0",
                "a2a-sdk >= 0.3.4",
                "pydantic==2.11.9",
                "cloudpickle==3.1.1",
                "langchain-google-genai>=2.0.10",
                "langchain-core>=0.3.76",
                "langchain-google-vertexai>=2.1.2",
                "langchain-mcp-adapters>=0.1.10",
                "langchain-openai>=0.3.33",
                "langgraph>=0.6.8",
                "pyowm==3.3.0",
                "timezonefinder==6.5.6"
            ],
            "http_options": {
                "base_url": f"https://{location}-aiplatform.googleapis.com",
                "api_version": "v1beta1",
            },
            "staging_bucket": f"gs://{bucket_name}",
            "env_vars": env_vars,
            "extra_packages": extra_packages
        }
    )
    logging.info(f"Deployed {agent_name} successfully: {remote_agent.api_resource.name}")
    return remote_agent.api_resource.name


def main():
    load_dotenv()
    
    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER")
    google_genai_model = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
    bucket_name = os.environ.get("BUCKET_NAME", f"{project_id}-bucket")

    if not project_id or not project_number:
        logging.error("PROJECT_ID and PROJECT_NUMBER must be set in environment.")
        return

    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket_name}")
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1", base_url=f"https://{location}-aiplatform.googleapis.com/"
        ),
    )

    ct_mcp_url = os.environ.get("CT_MCP_SERVER_URL")
    wea_mcp_url = os.environ.get("WEA_MCP_SERVER_URL")
    
    # Deploy Cocktail Agent
    ct_agent_name = deploy_agent(
        client,
        "Cocktail Agent",
        cocktail_agent_card,
        CocktailAgentExecutor,
        project_id,
        project_number,
        location,
        bucket_name,
        {
            "CT_MCP_SERVER_URL": ct_mcp_url,
            "GOOGLE_GENAI_MODEL": google_genai_model
        },
        ["src/a2a_agents/common/", "src/a2a_agents/cocktail_agent/"]
    )
    
    # Deploy Weather Agent
    wea_agent_name = deploy_agent(
        client,
        "Weather Agent",
        weather_agent_card,
        WeatherAgentExecutor,
        project_id,
        project_number,
        location,
        bucket_name,
        {
            "WEA_MCP_SERVER_URL": wea_mcp_url,
            "GOOGLE_GENAI_MODEL": google_genai_model,
            "OPENWEATHER_API_KEY": os.environ.get("OPENWEATHER_API_KEY", "")
        },
        ["src/a2a_agents/common/", "src/a2a_agents/weather_agent/"]
    )
    
    # Build URL endpoints for the agents based on their resource name
    ct_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{ct_agent_name}:query"
    wea_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{wea_agent_name}:query"
    
    # Deploy Hosting Agent
    host_agent_name = deploy_agent(
        client,
        "Hosting Agent",
        hosting_agent_card,
        HostingAgentExecutor,
        project_id,
        project_number,
        location,
        bucket_name,
        {
            "WEA_AGENT_URL": wea_agent_url,
            "CT_AGENT_URL": ct_agent_url,
            "GOOGLE_GENAI_MODEL": google_genai_model
        },
        ["src/a2a_agents/common/", "src/a2a_agents/hosting_agent/"]
    )
    
    logging.info(f"All agents deployed successfully.")

if __name__ == "__main__":
    main()

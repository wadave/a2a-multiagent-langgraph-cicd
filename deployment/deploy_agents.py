import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path for packaging logic so that a2a_agents are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import vertexai
from google.genai import types
from vertexai.preview.reasoning_engines import A2aAgent

from a2a_agents.cocktail_agent.cocktail_agent_card import cocktail_agent_card
from a2a_agents.cocktail_agent.agent_executor import CocktailAgentExecutor

from a2a_agents.weather_agent.weather_agent_card import weather_agent_card
from a2a_agents.weather_agent.agent_executor import WeatherAgentExecutor

from a2a_agents.hosting_agent.hosting_agent_card import hosting_agent_card
from a2a_agents.hosting_agent.langgraph_orchestrator_agent_executor import HostingAgentExecutor

from agent_state_manager import AgentStateManager

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

    # Vertex AI rejects empty string env var values
    env_vars = {k: v for k, v in env_vars.items() if v}

    logging.info(f"Deploying {agent_name} to Agent Engine...")

    # Ensure "a2a_agents" is always included in extra_packages
    if "a2a_agents" not in extra_packages:
        extra_packages.append("a2a_agents")

    remote_agent = client.agent_engines.create(
        agent=agent,
        config={
            "display_name": agent.agent_card.name,
            "description": agent.agent_card.description,
            "service_account": f"{project_number}-compute@developer.gserviceaccount.com",
            "requirements": [
                "a2a-sdk>=0.3.24",
                "google-adk>=1.25.1",
                "google-cloud-aiplatform[agent_engines,adk]>=1.130.0",
                "pydantic>=2.0.0",
                "cloudpickle==3.1.1",
                "langchain-google-genai>=2.0.10",
                "langchain-core>=0.3.76",
                "langchain-google-vertexai>=2.1.2",
                "langchain-mcp-adapters>=0.1.10",
                "langgraph>=0.6.8",
                "google-cloud-logging>=3.11.2"
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
    # Change current working directory to src so extra_packages path resolves correctly in Reasoning Engine
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
    os.chdir(src_dir)
    logging.info(f"Changed working directory to {src_dir}")

    load_dotenv()

    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER")
    google_genai_model = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
    bucket_name = os.environ.get("BUCKET_NAME", f"{project_id}-bucket")

    # Determine environment from branch or explicit env var
    environment = os.environ.get("ENVIRONMENT", "staging")
    state_manager = AgentStateManager(project_id, environment, location)

    if not project_id or not project_number:
        logging.error("PROJECT_ID and PROJECT_NUMBER must be set in environment.")
        sys.exit(1)

    ct_mcp_url = os.environ.get("CT_MCP_SERVER_URL")
    wea_mcp_url = os.environ.get("WEA_MCP_SERVER_URL")

    if not ct_mcp_url or not wea_mcp_url:
        logging.error("CT_MCP_SERVER_URL and WEA_MCP_SERVER_URL must be set in environment.")
        sys.exit(1)

    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket_name}")
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1", base_url=f"https://{location}-aiplatform.googleapis.com/"
        ),
    )

    deployed_agents = {}

    # Deploy Cocktail Agent
    try:
        ct_agent_name = deploy_agent(
            client,
            "Cocktail lg Agent",
            cocktail_agent_card,
            CocktailAgentExecutor,
            project_id,
            project_number,
            location,
            bucket_name,
            {
                "CT_MCP_SERVER_URL": ct_mcp_url,
                "PROJECT_NUMBER": project_number,
                "GOOGLE_CLOUD_LOCATION": location,
                "GOOGLE_GENAI_MODEL": google_genai_model
            },
            ["a2a_agents"]
        )
        deployed_agents["cocktail"] = ct_agent_name
        state_manager.update_agent("cocktail", ct_agent_name)
    except Exception as e:
        logging.error(f"Failed to deploy Cocktail Agent: {e}")
        sys.exit(1)

    # Deploy Weather Agent
    try:
        wea_agent_name = deploy_agent(
            client,
            "Weather lg Agent",
            weather_agent_card,
            WeatherAgentExecutor,
            project_id,
            project_number,
            location,
            bucket_name,
            {
                "WEA_MCP_SERVER_URL": wea_mcp_url,
                "PROJECT_NUMBER": project_number,
                "GOOGLE_CLOUD_LOCATION": location,
                "GOOGLE_GENAI_MODEL": google_genai_model
            },
            ["a2a_agents"]
        )
        deployed_agents["weather"] = wea_agent_name
        state_manager.update_agent("weather", wea_agent_name)
    except Exception as e:
        logging.error(f"Failed to deploy Weather Agent: {e}")
        sys.exit(1)

    # Build URL endpoints for the agents based on their resource name
    # Use A2A endpoints for LangGraph agents (not :query)
    ct_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{ct_agent_name}/a2a"
    wea_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{wea_agent_name}/a2a"

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
        deployed_agents["hosting"] = host_agent_name
        state_manager.update_agent("hosting", host_agent_name)
    except Exception as e:
        logging.error(f"Failed to deploy Hosting Agent: {e}")
        sys.exit(1)

    logging.info("All agents deployed successfully.")
    
    # Export the Hosting Agent ID to GITHUB_OUTPUT for the Frontend Cloud Run deployment
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"AGENT_ENGINE_ID={host_agent_name}\n")
        logging.info("Exported AGENT_ENGINE_ID to GITHUB_OUTPUT.")

if __name__ == "__main__":
    main()

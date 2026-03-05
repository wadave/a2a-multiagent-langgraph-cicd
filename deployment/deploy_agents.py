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
import os
import sys
import traceback
import tomllib
import logging
from pathlib import Path
from dotenv import load_dotenv

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


def get_agent_requirements() -> list[str]:
    """Read agent requirements from the [agents] optional-dependencies in pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["optional-dependencies"]["agents"]


def find_existing_agent(client, display_name):
    """Find an existing agent engine by display_name. Returns resource name if found."""
    try:
        for agent_engine in client.agent_engines.list():
            engine_display_name = (
                getattr(agent_engine.api_resource, 'display_name', '')
                or getattr(agent_engine.api_resource, 'displayName', '')
            )
            engine_name = getattr(agent_engine.api_resource, 'name', '')
            if engine_display_name == display_name:
                logging.info(f"Found existing agent engine '{display_name}': {engine_name}")
                return engine_name
    except Exception as e:
        logging.warning(f"Could not list agent engines: {e}")
    return None


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

    if "a2a_agents" not in extra_packages:
        extra_packages.append("a2a_agents")

    config = {
        "display_name": agent.agent_card.name,
        "description": agent.agent_card.description,
        "service_account": f"{project_number}-compute@developer.gserviceaccount.com",
        "requirements": get_agent_requirements(),
        "http_options": {
            "base_url": f"https://{location}-aiplatform.googleapis.com",
            "api_version": "v1beta1",
        },
        "staging_bucket": f"gs://{bucket_name}",
        "env_vars": env_vars,
        "extra_packages": extra_packages,
    }

    # Idempotent: update if exists, create if new
    existing_name = find_existing_agent(client, agent.agent_card.name)
    if existing_name:
        logging.info(f"Agent '{agent.agent_card.name}' already exists. Updating...")
        try:
            remote_agent = client.agent_engines.update(
                name=existing_name,
                agent=agent,
                config=config
            )
            logging.info(f"Updated {agent_name} successfully: {remote_agent.api_resource.name}")
            return remote_agent.api_resource.name
        except Exception as e:
            if "spec.package_spec" in str(e):
                logging.warning(f"Legacy package_spec detected for {agent.agent_card.name}. Deleting and recreating...")
                from google.genai.errors import ClientError
                try:
                    client.agent_engines.delete(name=existing_name, force=True)
                except Exception as del_e:
                    logging.warning(f"Error during legacy agent deletion: {del_e}")
            else:
                raise e

    remote_agent = client.agent_engines.create(
        agent=agent,
        config=config
    )

    # Fix backend bug: Vertex AI ignores displayName on creation, so patch immediately
    try:
        client.agent_engines.update(
            name=remote_agent.api_resource.name,
            config={
                "display_name": agent.agent_card.name,
                "description": agent.agent_card.description
            }
        )
        logging.info(f"Patched display name for {agent_name}")
    except Exception as patch_e:
        logging.warning(f"Failed to patch display name for {agent_name}: {patch_e}")

    logging.info(f"Deployed {agent_name} successfully: {remote_agent.api_resource.name}")
    return remote_agent.api_resource.name


def main():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
    os.chdir(src_dir)
    logging.info(f"Changed working directory to {src_dir}")

    load_dotenv()

    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER")
    google_genai_model = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
    bucket_name = os.environ.get("BUCKET_NAME", f"{project_id}-bucket")

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
                "GOOGLE_GENAI_MODEL": google_genai_model,
            },
            ["a2a_agents"],
        )
        deployed_agents["cocktail"] = ct_agent_name
        state_manager.update_agent("cocktail", ct_agent_name)
    except Exception as e:
        logging.error(f"Failed to deploy Cocktail Agent: {e}")
        traceback.print_exc()
        sys.exit(1)

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
                "GOOGLE_GENAI_MODEL": google_genai_model,
            },
            ["a2a_agents"],
        )
        deployed_agents["weather"] = wea_agent_name
        state_manager.update_agent("weather", wea_agent_name)
    except Exception as e:
        logging.error(f"Failed to deploy Weather Agent: {e}")
        traceback.print_exc()
        sys.exit(1)

    ct_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{ct_agent_name}/a2a"
    wea_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{wea_agent_name}/a2a"

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
                "GOOGLE_GENAI_MODEL": google_genai_model,
            },
            ["a2a_agents"],
        )
        deployed_agents["hosting"] = host_agent_name
        state_manager.update_agent("hosting", host_agent_name)
    except Exception as e:
        logging.error(f"Failed to deploy Hosting Agent: {e}")
        traceback.print_exc()
        sys.exit(1)

    logging.info("All agents deployed successfully.")

    # Write hosting agent ID to file for Cloud Build pipeline
    hosting_agent_id_file = os.environ.get("HOSTING_AGENT_ID_FILE")
    if hosting_agent_id_file:
        with open(hosting_agent_id_file, "w") as f:
            f.write(host_agent_name)
        logging.info(f"Wrote hosting agent ID to {hosting_agent_id_file}")

    # Also export to GITHUB_OUTPUT for backward compatibility
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"AGENT_ENGINE_ID={host_agent_name}\n")
        logging.info("Exported AGENT_ENGINE_ID to GITHUB_OUTPUT.")


if __name__ == "__main__":
    try:
        main()
    finally:
        logging.shutdown()

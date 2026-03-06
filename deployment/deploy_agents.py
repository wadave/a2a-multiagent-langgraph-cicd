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
"""Deploy all A2A agents to Vertex AI Agent Engine.

Uses AgentEngineConfig with source_packages to deploy agents via source_code_spec.
This is compatible with Terraform-created Agent Engine shells (which also use source_code_spec).

Environment variables:
    PROJECT_ID: GCP project ID for deployment
    PROJECT_NUMBER: GCP project number
    GOOGLE_CLOUD_REGION: GCP region (default: us-central1)
    CT_MCP_SERVER_URL: Cocktail MCP server URL
    WEA_MCP_SERVER_URL: Weather MCP server URL
    ENVIRONMENT: Deployment environment (staging/prod)
    BUCKET_NAME: GCS bucket for staging (default: {PROJECT_ID}-bucket)
    GOOGLE_GENAI_MODEL: Model name (default: gemini-2.5-flash)
"""

import importlib
import logging
import os
import sys
import tomllib
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import vertexai
from agent_state_manager import AgentStateManager
from vertexai._genai import _agent_engines_utils
from vertexai._genai.types import AgentEngineConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_class_methods_from_agent(agent_instance: Any) -> list[dict[str, Any]]:
    """Generate method specifications with schemas from agent's register_operations()."""
    registered_operations = _agent_engines_utils._get_registered_operations(
        agent=agent_instance
    )
    class_methods_spec = _agent_engines_utils._generate_class_methods_spec_or_raise(
        agent=agent_instance,
        operations=registered_operations,
    )
    class_methods_list = [
        _agent_engines_utils._to_dict(method_spec) for method_spec in class_methods_spec
    ]
    return class_methods_list


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
            engine_display_name = getattr(agent_engine.api_resource, "display_name", "") or getattr(
                agent_engine.api_resource, "displayName", ""
            )
            engine_name = getattr(agent_engine.api_resource, "name", "")
            if engine_display_name == display_name:
                logger.info(f"Found existing agent engine '{display_name}': {engine_name}")
                return engine_name
    except Exception as e:
        logger.warning(f"Could not list agent engines: {e}")
    return None


def deploy_agent(
    client,
    display_name,
    description,
    entrypoint_module,
    entrypoint_object,
    service_account,
    env_vars,
    requirements_file: str,
):
    """Deploy or update an agent using AgentEngineConfig (source_code_spec compatible)."""

    logger.info(f"Importing {entrypoint_module}.{entrypoint_object}")
    module = importlib.import_module(entrypoint_module)
    agent_instance = getattr(module, entrypoint_object)
    class_methods_list = generate_class_methods_from_agent(agent_instance)

    if requirements_file:
        logger.info(f"Using requirements file: {requirements_file}")

    config = AgentEngineConfig(
        display_name=display_name,
        description=description,
        source_packages=["./a2a_agents"],
        entrypoint_module=entrypoint_module,
        entrypoint_object=entrypoint_object,
        class_methods=class_methods_list,
        requirements_file=requirements_file,
        env_vars={k: v for k, v in env_vars.items() if v},
        service_account=service_account,
    )

    existing_name = find_existing_agent(client, display_name)
    if existing_name:
        logger.info(f"Updating existing agent '{display_name}': {existing_name}")
        try:
            remote_agent = client.agent_engines.update(
                name=existing_name,
                config=config,
            )
        except Exception as e:
            logger.warning(
                f"Agent engine update failed: {e}. Falling back to delete and recreate '{display_name}' ({existing_name})..."
            )
            # Fallback: Delete and recreate
            client.agent_engines.delete(name=existing_name)
            logger.info(f"Creating new agent '{display_name}' after deletion...")
            remote_agent = client.agent_engines.create(config=config)
        logger.info(f"Updated '{display_name}' successfully: {remote_agent.api_resource.name}")
        return remote_agent.api_resource.name

    logger.info(f"Creating new agent '{display_name}'...")
    remote_agent = client.agent_engines.create(config=config)
    logger.info(f"Created '{display_name}' successfully: {remote_agent.api_resource.name}")
    return remote_agent.api_resource.name


def main():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
    os.chdir(src_dir)
    logger.info(f"Changed working directory to {src_dir}")

    load_dotenv()

    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    project_number = os.environ.get("PROJECT_NUMBER")
    google_genai_model = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
    bucket_name = os.environ.get("BUCKET_NAME", f"{project_id}-bucket")
    environment = os.environ.get("ENVIRONMENT", "staging")
    state_manager = AgentStateManager(project_id, environment, location)
    
    # Use the app service account created by Terraform: a2a-multiagent-lg-cicd-app
    service_account = f"a2a-multiagent-lg-cicd-app@{project_id}.iam.gserviceaccount.com"

    if not project_id or not project_number:
        logger.error("PROJECT_ID and PROJECT_NUMBER must be set in environment.")
        sys.exit(1)

    ct_mcp_url = os.environ.get("CT_MCP_SERVER_URL")
    wea_mcp_url = os.environ.get("WEA_MCP_SERVER_URL")

    if not ct_mcp_url or not wea_mcp_url:
        logger.error("CT_MCP_SERVER_URL and WEA_MCP_SERVER_URL must be set in environment.")
        sys.exit(1)

    requirements = get_agent_requirements()
    
    requirements_path = os.path.join(src_dir, "a2a_agents", ".requirements.txt")
    with open(requirements_path, "w") as f:
        f.write("\n".join(requirements))
    logger.info(f"Wrote requirements to {requirements_path}")
    
    # We pass the relative path as expected by vertex SDK for remote bundling
    rel_req_path = "a2a_agents/.requirements.txt"

    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket_name}")
    client = vertexai.Client(project=project_id, location=location)

    base_env = {
        "PROJECT_ID": project_id,
        "LOCATION": location,
        "BUCKET": bucket_name,
        "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
        "PROJECT_NUMBER": project_number,
        "GOOGLE_CLOUD_LOCATION": location,
        "GOOGLE_GENAI_MODEL": google_genai_model,
    }

    # --- Deploy Cocktail Agent ---
    try:
        ct_env = {**base_env, "CT_MCP_SERVER_URL": ct_mcp_url}
        ct_agent_name = deploy_agent(
            client,
            display_name="Cocktail Agent LangGraph",
            description="A2A agent for cocktail information",
            entrypoint_module="a2a_agents.cocktail_agent.agent_engine_app",
            entrypoint_object="agent_engine",
            service_account=service_account,
            env_vars=ct_env,
            requirements_file=rel_req_path,
        )
        state_manager.update_agent("cocktail", ct_agent_name)
    except Exception as e:
        logger.error(f"Failed to deploy Cocktail Agent: {e}")
        traceback.print_exc()
        sys.exit(1)

    # --- Deploy Weather Agent ---
    try:
        wea_env = {**base_env, "WEA_MCP_SERVER_URL": wea_mcp_url}
        wea_agent_name = deploy_agent(
            client,
            display_name="Weather Agent LangGraph",
            description="A2A agent for weather forecasts",
            entrypoint_module="a2a_agents.weather_agent.agent_engine_app",
            entrypoint_object="agent_engine",
            service_account=service_account,
            env_vars=wea_env,
            requirements_file=rel_req_path,
        )
        state_manager.update_agent("weather", wea_agent_name)
    except Exception as e:
        logger.error(f"Failed to deploy Weather Agent: {e}")
        traceback.print_exc()
        sys.exit(1)

    # --- Deploy Hosting Agent ---
    ct_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{ct_agent_name}/a2a"
    wea_agent_url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{wea_agent_name}/a2a"

    try:
        host_env = {**base_env, "CT_AGENT_URL": ct_agent_url, "WEA_AGENT_URL": wea_agent_url}
        host_agent_name = deploy_agent(
            client,
            display_name="Hosting Agent LangGraph",
            description="Orchestrator agent that delegates to specialist agents",
            entrypoint_module="a2a_agents.hosting_agent.agent_engine_app",
            entrypoint_object="agent_engine",
            service_account=service_account,
            env_vars=host_env,
            requirements_file=".requirements.txt",
        )
        state_manager.update_agent("hosting", host_agent_name)
    except Exception as e:
        logger.error(f"Failed to deploy Hosting Agent: {e}")
        traceback.print_exc()
        sys.exit(1)

    logger.info("All agents deployed successfully.")

    # Write hosting agent ID to file for Cloud Build pipeline
    hosting_agent_id_file = os.environ.get("HOSTING_AGENT_ID_FILE")
    if hosting_agent_id_file:
        with open(hosting_agent_id_file, "w") as f:
            f.write(host_agent_name)
        logger.info(f"Wrote hosting agent ID to {hosting_agent_id_file}")

    # Also export to GITHUB_OUTPUT for backward compatibility
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"AGENT_ENGINE_ID={host_agent_name}\n")
        logger.info("Exported AGENT_ENGINE_ID to GITHUB_OUTPUT.")


if __name__ == "__main__":
    try:
        main()
    finally:
        logging.shutdown()
# Trigger deployment

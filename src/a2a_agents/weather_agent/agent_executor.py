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
# Author: Dave Wang
import os
from typing import Any

from a2a_agents.common.langgraph_base_mcp_agent_executor import (
    LanggraphBaseMCPAgentExecutor,
)
from a2a_agents.weather_agent.agent import WeatherAgent


class WeatherAgentExecutor(LanggraphBaseMCPAgentExecutor):
    """Weather Agent Executor."""

    def get_mcp_server_url(self) -> str:
        """Return the MCP server URL for Weather agent."""
        # Try environment variable first
        if "WEA_MCP_SERVER_URL" in os.environ:
            return os.environ["WEA_MCP_SERVER_URL"]

        # Otherwise construct from project number and region env vars
        project_number = os.environ.get("PROJECT_NUMBER")
        region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        return f"https://weather-remote-mcp-server-lg-{project_number}.{region}.run.app/mcp/"

    def get_mcp_server_name(self) -> str:
        """Return the MCP server name for Weather agent."""
        return "Weather"

    def create_agent(self, mcp_tools: list[Any]) -> WeatherAgent:
        """Create and return the WeatherAgent instance."""
        return WeatherAgent(mcp_tools=mcp_tools)

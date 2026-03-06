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

import httpx
import pytest
from fastmcp.client import Client
from google.auth.transport.requests import Request as AuthRequest
from google.oauth2 import id_token

WEATHER_MCP_URL = os.environ.get(
    "WEATHER_MCP_URL", "https://weather-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp"
)


def get_auth_token(url):
    try:
        # Strip /sse or /mcp/sse for audience if present
        audience = url.replace("/mcp/sse", "").replace("/sse", "")
        # Also remove trailing slash if any
        if audience.endswith("/"):
            audience = audience[:-1]

        auth_req = AuthRequest()
        return id_token.fetch_id_token(auth_req, audience)
    except Exception as e:
        print(f"Warning: Could not fetch ID token: {e}")
        return None


class BearerAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


@pytest.mark.integration
async def test_weather_mcp_list_tools():
    """Verify the weather MCP server exposes expected tools."""
    token = get_auth_token(WEATHER_MCP_URL)
    auth = BearerAuth(token) if token else None

    async with Client(WEATHER_MCP_URL, auth=auth) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "get_active_alerts_by_state" in tool_names
        assert "get_forecast" in tool_names
        assert "get_forecast_by_city" in tool_names


@pytest.mark.integration
async def test_weather_mcp_get_forecast_by_city():
    """Verify get_forecast_by_city returns forecast data for New York, NY."""
    token = get_auth_token(WEATHER_MCP_URL)
    auth = BearerAuth(token) if token else None

    async with Client(WEATHER_MCP_URL, auth=auth) as client:
        result = await client.call_tool("get_forecast_by_city", {"city": "New York", "state": "NY"})
        assert len(result) > 0
        assert result[0].text

import os

import pytest
import httpx
from fastmcp.client import Client
from google.oauth2 import id_token
from google.auth.transport.requests import Request as AuthRequest

WEATHER_MCP_URL = os.environ.get("WEATHER_MCP_URL", "https://weather-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp")

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
        request.headers['Authorization'] = f"Bearer {self.token}"
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
        result = await client.call_tool(
            "get_forecast_by_city", {"city": "New York", "state": "NY"}
        )
        assert len(result) > 0
        assert result[0].text

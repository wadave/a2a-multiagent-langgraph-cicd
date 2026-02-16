import os

import pytest
from fastmcp.client import Client

WEATHER_MCP_URL = os.environ.get("WEATHER_MCP_URL", "http://localhost:8080/mcp")


@pytest.mark.integration
async def test_weather_mcp_list_tools():
    """Verify the weather MCP server exposes expected tools."""
    async with Client(WEATHER_MCP_URL) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "get_active_alerts_by_state" in tool_names
        assert "get_forecast" in tool_names
        assert "get_forecast_by_city" in tool_names


@pytest.mark.integration
async def test_weather_mcp_get_forecast_by_city():
    """Verify get_forecast_by_city returns forecast data for New York, NY."""
    async with Client(WEATHER_MCP_URL) as client:
        result = await client.call_tool(
            "get_forecast_by_city", {"city": "New York", "state": "NY"}
        )
        assert len(result) > 0
        assert result[0].text

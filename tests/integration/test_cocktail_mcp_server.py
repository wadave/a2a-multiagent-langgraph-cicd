import os

import pytest
from fastmcp.client import Client

COCKTAIL_MCP_URL = os.environ.get("COCKTAIL_MCP_URL", "http://localhost:8080/mcp")


@pytest.mark.integration
async def test_cocktail_mcp_list_tools():
    """Verify the cocktail MCP server exposes expected tools."""
    async with Client(COCKTAIL_MCP_URL) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "search_cocktail_by_name" in tool_names
        assert "list_cocktails_by_first_letter" in tool_names
        assert "search_ingredient_by_name" in tool_names
        assert "list_random_cocktails" in tool_names
        assert "lookup_cocktail_details_by_id" in tool_names


@pytest.mark.integration
async def test_cocktail_mcp_search_by_name():
    """Verify search_cocktail_by_name returns results for 'margarita'."""
    async with Client(COCKTAIL_MCP_URL) as client:
        result = await client.call_tool(
            "search_cocktail_by_name", {"name": "margarita"}
        )
        assert len(result) > 0
        assert result[0].text
        assert "margarita" in result[0].text.lower()

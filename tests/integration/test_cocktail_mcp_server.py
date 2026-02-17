import os

import pytest
import httpx
from fastmcp.client import Client
from google.oauth2 import id_token
from google.auth.transport.requests import Request as AuthRequest

COCKTAIL_MCP_URL = os.environ.get("COCKTAIL_MCP_URL", "https://cocktail-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp")

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
async def test_cocktail_mcp_list_tools():
    """Verify the cocktail MCP server exposes expected tools."""
    token = get_auth_token(COCKTAIL_MCP_URL)
    auth = BearerAuth(token) if token else None
    
    async with Client(COCKTAIL_MCP_URL, auth=auth) as client:
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
    token = get_auth_token(COCKTAIL_MCP_URL)
    auth = BearerAuth(token) if token else None

    async with Client(COCKTAIL_MCP_URL, auth=auth) as client:
        result = await client.call_tool(
            "search_cocktail_by_name", {"name": "margarita"}
        )
        assert len(result) > 0
        assert result[0].text
        assert "margarita" in result[0].text.lower()

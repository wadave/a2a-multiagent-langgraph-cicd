import asyncio
import os
import httpx
import google.auth.transport.requests
from google.oauth2 import id_token
from fastmcp import Client
import subprocess

# MCP Server URLs - Updated to match LangGraph (-lg) services
# Added trailing slash to avoid potential redirects that strip auth headers
COCKTAIL_SERVER_URL = "https://cocktail-remote-mcp-server-lg-496235138247.us-central1.run.app/"
WEATHER_SERVER_URL = "https://weather-remote-mcp-server-lg-496235138247.us-central1.run.app/"

class BearerAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

def get_id_token(url):
    """Generates an ID token for the given URL."""
    # Strip the scheme and just use the hostname if needed, but gcloud usually handles full URLs
    # Remove /mcp/ if it exists in the URL for audience
    audience = url.split("/mcp")[0]
    if audience.endswith("/"):
        audience = audience[:-1]

    # Try fetching via gcloud first with explicit audience
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token", f"--audiences={audience}"], text=True
        ).strip()
        if token:
            return token
    except Exception as e:
        print(f"gcloud auth with audiences failed: {e}")
        pass

    # Fallback to google-auth (handles Service Accounts / GCE Metadata)
    auth_req = google.auth.transport.requests.Request()
    return id_token.fetch_id_token(auth_req, audience)

async def test_cocktail_server():
    """Tests the Cocktail MCP server."""
    print("\n--- Testing Cocktail MCP Server ---")
    auth = None  # Try without auth first (service allows allUsers)
    # try:
    #     token = get_id_token(COCKTAIL_SERVER_URL)
    #     auth = BearerAuth(token)
    # except Exception as e:
    #     print(f"Warning: Could not get ID token: {e}")
    #     auth = None

    # Use the /mcp endpoint
    endpoint = f"{COCKTAIL_SERVER_URL}mcp/"

    print(f"Connecting to: {endpoint} (no auth)")
    async with Client(endpoint, auth=auth) as client:
        # List available tools
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> 🛠️  Tool found: {tool.name}")
        
        # Call search tool
        print("Calling search_cocktail_by_name('margarita')...")
        result = await client.call_tool(
            "search_cocktail_by_name", {"name": "margarita"}
        )
        if hasattr(result, 'content') and result.content:
            print(f"<<< ✅ Result: {result.content[0].text[:200]}...")
        else:
            print(f"<<< ✅ Result: {result}")

async def test_weather_server():
    """Tests the Weather MCP server."""
    print("\n--- Testing Weather MCP Server ---")
    auth = None  # Try without auth first (service allows allUsers)
    # try:
    #     token = get_id_token(WEATHER_SERVER_URL)
    #     auth = BearerAuth(token)
    # except Exception as e:
    #     print(f"Warning: Could not get ID token: {e}")
    #     auth = None

    endpoint = f"{WEATHER_SERVER_URL}mcp/"
    print(f"Connecting to: {endpoint} (no auth)")
    
    async with Client(endpoint, auth=auth) as client:
        # List available tools
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> 🛠️  Tool found: {tool.name}")
        
        # Call forecast tool
        print("Calling get_forecast_by_city('New York', 'NY')...")
        result = await client.call_tool(
            "get_forecast_by_city", {"city": "New York", "state": "NY"}
        )
        if hasattr(result, 'content') and result.content:
            print(f"<<< ✅ Result: {result.content[0].text[:200]}...")
        else:
            print(f"<<< ✅ Result: {result}")

async def main():
    try:
        await test_cocktail_server()
        await test_weather_server()
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Ensure you have authenticated with 'gcloud auth application-default login'")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

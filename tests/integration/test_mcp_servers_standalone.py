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
#!/usr/bin/env python3
"""Standalone test for MCP servers."""

import asyncio
import httpx
from fastmcp.client import Client
from google.oauth2 import id_token
from google.auth.transport.requests import Request as AuthRequest

COCKTAIL_MCP_URL = "https://cocktail-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp"
WEATHER_MCP_URL = "https://weather-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp"

def get_auth_token(url):
    try:
        # Strip /mcp for audience
        audience = url.replace("/mcp", "")
        if audience.endswith("/"):
            audience = audience[:-1]

        auth_req = AuthRequest()
        token = id_token.fetch_id_token(auth_req, audience)
        print(f"✓ Got auth token for {audience}")
        return token
    except Exception as e:
        print(f"✗ Could not fetch ID token: {e}")
        return None

class BearerAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token

    def auth_flow(self, request):
        request.headers['Authorization'] = f"Bearer {self.token}"
        yield request

async def test_cocktail_mcp():
    print("\n" + "="*60)
    print("Testing Cocktail MCP Server")
    print("="*60)
    print(f"URL: {COCKTAIL_MCP_URL}\n")

    token = get_auth_token(COCKTAIL_MCP_URL)
    auth = BearerAuth(token) if token else None

    try:
        async with Client(COCKTAIL_MCP_URL, auth=auth) as client:
            # Test 1: List tools
            print("Test 1: Listing tools...")
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"✓ Found {len(tools)} tools:")
            for name in tool_names:
                print(f"  - {name}")

            expected_tools = [
                "search_cocktail_by_name",
                "list_cocktails_by_first_letter",
                "search_ingredient_by_name",
                "list_random_cocktails",
                "lookup_cocktail_details_by_id"
            ]

            missing = [t for t in expected_tools if t not in tool_names]
            if missing:
                print(f"✗ Missing tools: {missing}")
                return False
            print(f"✓ All expected tools present\n")

            # Test 2: Search for margarita
            print("Test 2: Searching for 'margarita'...")
            result = await client.call_tool(
                "search_cocktail_by_name", {"name": "margarita"}
            )

            if not result:
                print("✗ No results returned")
                return False

            print(f"✓ Got {len(result)} result(s)")
            if result[0].text:
                preview = result[0].text[:200] + "..." if len(result[0].text) > 200 else result[0].text
                print(f"  Preview: {preview}")

            if "margarita" not in result[0].text.lower():
                print("✗ Result doesn't contain 'margarita'")
                return False

            print("✓ Result contains 'margarita'\n")

            print("="*60)
            print("✓ Cocktail MCP Server - ALL TESTS PASSED")
            print("="*60)
            return True

    except Exception as e:
        print(f"\n✗ Error testing cocktail MCP: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_weather_mcp():
    print("\n" + "="*60)
    print("Testing Weather MCP Server")
    print("="*60)
    print(f"URL: {WEATHER_MCP_URL}\n")

    token = get_auth_token(WEATHER_MCP_URL)
    auth = BearerAuth(token) if token else None

    try:
        async with Client(WEATHER_MCP_URL, auth=auth) as client:
            # Test 1: List tools
            print("Test 1: Listing tools...")
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"✓ Found {len(tools)} tools:")
            for name in tool_names:
                print(f"  - {name}")

            expected_tools = [
                "get_active_alerts_by_state",
                "get_forecast",
                "get_forecast_by_city"
            ]

            missing = [t for t in expected_tools if t not in tool_names]
            if missing:
                print(f"✗ Missing tools: {missing}")
                return False
            print(f"✓ All expected tools present\n")

            # Test 2: Get forecast for New York
            print("Test 2: Getting forecast for 'New York, NY'...")
            result = await client.call_tool(
                "get_forecast_by_city", {"city": "New York", "state": "NY"}
            )

            if not result:
                print("✗ No results returned")
                return False

            print(f"✓ Got {len(result)} result(s)")
            if result[0].text:
                preview = result[0].text[:200] + "..." if len(result[0].text) > 200 else result[0].text
                print(f"  Preview: {preview}")

            print("✓ Forecast data received\n")

            print("="*60)
            print("✓ Weather MCP Server - ALL TESTS PASSED")
            print("="*60)
            return True

    except Exception as e:
        print(f"\n✗ Error testing weather MCP: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n" + "="*60)
    print("MCP SERVER TESTS")
    print("="*60)

    cocktail_result = await test_cocktail_mcp()
    weather_result = await test_weather_mcp()

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Cocktail MCP Server: {'✓ PASS' if cocktail_result else '✗ FAIL'}")
    print(f"Weather MCP Server:  {'✓ PASS' if weather_result else '✗ FAIL'}")
    print("="*60)

    if cocktail_result and weather_result:
        print("\n✓ ALL MCP SERVERS WORKING!")
        return 0
    else:
        print("\n✗ Some MCP servers failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

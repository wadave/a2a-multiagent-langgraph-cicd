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
"""Test the deployed Gradio frontend on Cloud Run."""

import requests

FRONTEND_URL = "https://a2a-frontend-496235138247.us-central1.run.app"


def test_frontend_health():
    """Test if the frontend is accessible."""
    print(f"Testing frontend at {FRONTEND_URL}...")

    try:
        response = requests.get(FRONTEND_URL, timeout=30)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✓ Frontend is accessible!")
            # Check if it's the Gradio interface
            if "gradio" in response.text.lower() or "a2a host agent" in response.text.lower():
                print("✓ Gradio interface detected!")
                return True
            else:
                print("⚠ Response received but may not be the Gradio interface")
                return False
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error accessing frontend: {e}")
        return False


def test_gradio_api():
    """Test Gradio API endpoint."""
    print("\nTesting Gradio API...")

    try:
        # Gradio exposes a /config endpoint
        config_url = f"{FRONTEND_URL}/config"
        response = requests.get(config_url, timeout=30)

        if response.status_code == 200:
            print("✓ Gradio API is responding!")
            print(f"Response preview: {response.text[:200]}...")
            return True
        else:
            print(f"⚠ Config endpoint returned {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠ Could not access Gradio API: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Deployed Frontend on Cloud Run")
    print("=" * 60)

    health_ok = test_frontend_health()
    api_ok = test_gradio_api()

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"Frontend Health: {'PASS' if health_ok else 'FAIL'}")
    print(f"Gradio API: {'PASS' if api_ok else 'FAIL'}")
    print(f"\nFrontend URL: {FRONTEND_URL}")
    print("Open this URL in your browser to interact with the chat interface!")
    print("=" * 60)

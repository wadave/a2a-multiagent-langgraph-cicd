#!/usr/bin/env python3
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
"""Comprehensive load testing for A2A multi-agent system."""

import logging
import os
import random
import time

from locust import HttpUser, between, task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
PROJECT_NUMBER = os.environ.get("PROJECT_NUMBER")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
AGENT_ENGINE_ID = os.environ.get("AGENT_ENGINE_ID")

if not PROJECT_ID or not PROJECT_NUMBER or not AGENT_ENGINE_ID:
    raise ValueError("PROJECT_ID, PROJECT_NUMBER, and AGENT_ENGINE_ID must be set")

# Convert to streaming URL
base_url = f"https://{LOCATION}-aiplatform.googleapis.com"
url_path = f"/v1beta1/projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}:streamQuery"

logger.info("Load Test Configuration:")
logger.info(f"  Project: {PROJECT_ID}")
logger.info(f"  Location: {LOCATION}")
logger.info(f"  Agent Engine ID: {AGENT_ENGINE_ID}")
logger.info(f"  Base URL: {base_url}")


# Test queries for different scenarios
WEATHER_QUERIES = [
    "What's the weather in New York?",
    "Get forecast for Los Angeles, CA",
    "Are there any weather alerts in Texas?",
    "What's the weather forecast for Seattle?",
    "Tell me the weather in Miami",
]

COCKTAIL_QUERIES = [
    "What are the ingredients for a Margarita?",
    "Give me a random cocktail",
    "Find cocktails starting with M",
    "Search for vodka as an ingredient",
    "How do I make a Manhattan?",
]

MULTI_AGENT_QUERIES = [
    "What's the weather in Miami and what cocktail should I drink there?",
    "Is it raining in Seattle and can you suggest a warm drink?",
    "Tell me the forecast for New York and recommend a cocktail",
]

GENERAL_QUERIES = [
    "Hello, how are you?",
    "What can you help me with?",
    "Tell me about your capabilities",
]


class HostingAgentUser(HttpUser):
    """Simulates a user interacting with the hosting agent."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = base_url

    def on_start(self):
        """Initialize user session."""
        self.user_session_id = f"load_test_session_{random.randint(1000, 9999)}"
        logger.info(f"Starting session {self.user_session_id}")

    @task(3)
    def test_weather_query(self):
        """Test weather-related queries."""
        query = random.choice(WEATHER_QUERIES)
        self._send_query(query, "weather")

    @task(3)
    def test_cocktail_query(self):
        """Test cocktail-related queries."""
        query = random.choice(COCKTAIL_QUERIES)
        self._send_query(query, "cocktail")

    @task(2)
    def test_multi_agent_query(self):
        """Test queries requiring multiple agents."""
        query = random.choice(MULTI_AGENT_QUERIES)
        self._send_query(query, "multi-agent")

    @task(1)
    def test_general_query(self):
        """Test general conversation queries."""
        query = random.choice(GENERAL_QUERIES)
        self._send_query(query, "general")

    def _send_query(self, message_text: str, category: str):
        """Send a query to the hosting agent.

        Args:
            message_text: The query message text
            category: Category of the query for metrics
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('_AUTH_TOKEN', '')}",
        }

        # The :streamQuery endpoint expects class_method and input
        data = {
            "class_method": "async_stream_query",
            "input": {"message": {"role": "ROLE_USER", "parts": [{"text": message_text}]}},
        }

        start_time = time.time()
        request_name = f":streamQuery {category}"

        try:
            with self.client.post(
                url_path,
                headers=headers,
                json=data,
                catch_response=True,
                name=request_name,
                stream=True,
                params={"alt": "sse"},
            ) as response:
                if response.status_code == 200:
                    total_time = (time.time() - start_time) * 1000
                    logger.debug(
                        f"Successful {category} streaming query: {message_text[:50]}... "
                        f"(took {total_time:.0f}ms)"
                    )
                    # Consume stream
                    for _ in response.iter_lines():
                        pass
                    response.success()
                else:
                    logger.error(f"Status {response.status_code} for {category}: {response.text}")
                    response.failure(f"Status {response.status_code}")

        except Exception as e:
            logger.error(f"Exception in {category} query: {e}")
            self.environment.events.request.fire(
                request_type="POST",
                name=request_name,
                response_time=0,
                response_length=0,
                exception=e,
                context={},
            )


class MixedLoadUser(HttpUser):
    """User with mixed query patterns simulating real usage."""

    wait_time = between(2, 5)
    host = base_url

    def on_start(self):
        """Initialize user session."""
        self.user_id = f"mixed_user_{random.randint(1000, 9999)}"
        self.query_count = 0

    @task
    def realistic_conversation(self):
        """Simulate a realistic conversation pattern."""
        # Start with greeting
        if self.query_count == 0:
            query = "Hello"
        # Then ask about capabilities
        elif self.query_count == 1:
            query = "What can you help me with?"
        # Then ask specific questions
        else:
            query_type = random.choice(["weather", "cocktail", "multi"])
            if query_type == "weather":
                query = random.choice(WEATHER_QUERIES)
            elif query_type == "cocktail":
                query = random.choice(COCKTAIL_QUERIES)
            else:
                query = random.choice(MULTI_AGENT_QUERIES)

        self.query_count += 1
        self._send_query(query, "realistic")

    def _send_query(self, message_text: str, category: str):
        """Send query (same implementation as HostingAgentUser)."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('_AUTH_TOKEN', '')}",
        }

        data = {
            "class_method": "async_stream_query",
            "input": {"message": {"role": "ROLE_USER", "parts": [{"text": message_text}]}},
        }

        with self.client.post(
            url_path,
            headers=headers,
            json=data,
            catch_response=True,
            name=f":streamQuery {category}",
            stream=True,
            params={"alt": "sse"},
        ) as response:
            if response.status_code == 200:
                for _ in response.iter_lines():
                    pass
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

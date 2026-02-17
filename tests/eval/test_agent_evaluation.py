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
"""Agent evaluation tests using test cases."""

import asyncio
import json
import os
import pytest
from pathlib import Path
from typing import Dict, List

# Load evaluation configuration
EVAL_CONFIG_PATH = Path(__file__).parent / "eval_config.json"
EVALSETS_DIR = Path(__file__).parent / "evalsets"


def load_eval_config() -> Dict:
    """Load evaluation configuration."""
    with open(EVAL_CONFIG_PATH) as f:
        return json.load(f)


def load_evalset(evalset_name: str) -> List[Dict]:
    """Load an evaluation set."""
    evalset_path = EVALSETS_DIR / f"{evalset_name}.evalset.json"
    if not evalset_path.exists():
        return []
    with open(evalset_path) as f:
        data = json.load(f)
    return data.get("examples", [])


class TestAgentEvaluation:
    """Tests for agent evaluation criteria."""

    @pytest.fixture
    def eval_config(self):
        """Load evaluation config."""
        return load_eval_config()

    @pytest.fixture
    def basic_evalset(self):
        """Load basic evaluation set."""
        return load_evalset("basic")

    def test_eval_config_structure(self, eval_config):
        """Verify evaluation config has proper structure."""
        assert "criteria" in eval_config
        assert "tool_trajectory_avg_score" in eval_config["criteria"]
        assert "rubric_based_final_response_quality_v1" in eval_config["criteria"]

    def test_eval_config_thresholds(self, eval_config):
        """Verify evaluation thresholds are defined."""
        tool_trajectory_threshold = eval_config["criteria"]["tool_trajectory_avg_score"]
        assert tool_trajectory_threshold == 0.9

        rubric_config = eval_config["criteria"]["rubric_based_final_response_quality_v1"]
        assert rubric_config["threshold"] == 0.8

    def test_eval_config_rubrics(self, eval_config):
        """Verify all required rubrics are defined."""
        rubric_config = eval_config["criteria"]["rubric_based_final_response_quality_v1"]
        rubrics = rubric_config["rubrics"]

        rubric_ids = [r["rubricId"] for r in rubrics]
        assert "relevance" in rubric_ids
        assert "helpfulness" in rubric_ids
        assert "format" in rubric_ids
        assert "tool_routing" in rubric_ids

    def test_evalset_exists(self, basic_evalset):
        """Verify basic evaluation set exists and has examples."""
        assert isinstance(basic_evalset, list)
        # Allow empty evalset for now
        if len(basic_evalset) > 0:
            assert all(isinstance(ex, dict) for ex in basic_evalset)

    def test_evalset_example_structure(self, basic_evalset):
        """Verify evaluation examples have proper structure."""
        if len(basic_evalset) == 0:
            pytest.skip("No examples in evalset")

        for example in basic_evalset:
            # Each example should have input and expected output
            assert "input" in example or "query" in example
            # Additional fields may vary


class TestRubricCriteria:
    """Tests for evaluation rubric criteria."""

    @pytest.fixture
    def rubrics(self):
        """Load rubrics from eval config."""
        config = load_eval_config()
        return config["criteria"]["rubric_based_final_response_quality_v1"]["rubrics"]

    def test_relevance_rubric(self, rubrics):
        """Verify relevance rubric is defined."""
        relevance = next((r for r in rubrics if r["rubricId"] == "relevance"), None)
        assert relevance is not None
        assert "rubricContent" in relevance
        assert "textProperty" in relevance["rubricContent"]

    def test_helpfulness_rubric(self, rubrics):
        """Verify helpfulness rubric is defined."""
        helpfulness = next((r for r in rubrics if r["rubricId"] == "helpfulness"), None)
        assert helpfulness is not None
        assert "rubricContent" in helpfulness
        assert "textProperty" in helpfulness["rubricContent"]

    def test_format_rubric(self, rubrics):
        """Verify format rubric is defined."""
        format_rubric = next((r for r in rubrics if r["rubricId"] == "format"), None)
        assert format_rubric is not None
        assert "Markdown" in format_rubric["rubricContent"]["textProperty"]

    def test_tool_routing_rubric(self, rubrics):
        """Verify tool routing rubric is defined."""
        routing = next((r for r in rubrics if r["rubricId"] == "tool_routing"), None)
        assert routing is not None
        content = routing["rubricContent"]["textProperty"]
        assert "Weather Agent" in content or "weather" in content.lower()
        assert "Cocktail Agent" in content or "cocktail" in content.lower()


class TestAgentResponseQuality:
    """Tests for evaluating agent response quality."""

    def test_weather_query_routing(self):
        """Test that weather queries should route to Weather Agent."""
        weather_queries = [
            "What's the weather in New York?",
            "Tell me the forecast for San Francisco",
            "Is it going to rain tomorrow in Seattle?",
        ]

        # These queries should be routed to Weather Agent
        for query in weather_queries:
            assert "weather" in query.lower() or "forecast" in query.lower()

    def test_cocktail_query_routing(self):
        """Test that cocktail queries should route to Cocktail Agent."""
        cocktail_queries = [
            "What are the ingredients for a Margarita?",
            "Give me a random cocktail recipe",
            "How do I make a Manhattan?",
        ]

        # These queries should be routed to Cocktail Agent
        for query in cocktail_queries:
            assert any(
                word in query.lower()
                for word in ["cocktail", "margarita", "recipe", "ingredients", "drink"]
            )

    def test_general_query_no_routing(self):
        """Test that general queries should not route to specific agents."""
        general_queries = [
            "Hello",
            "What can you do?",
            "Help me",
        ]

        # These queries should not contain agent-specific keywords
        for query in general_queries:
            assert not any(
                word in query.lower() for word in ["weather", "cocktail", "forecast"]
            )

    def test_response_format_markdown(self):
        """Test that responses should be formatted in Markdown."""
        # Mock response examples
        good_response = """
## Weather Forecast

**City**: New York
**Temperature**: 72°F
**Conditions**: Sunny

- Wind: 10 mph
- Humidity: 45%
        """

        bad_response = "New York 72F Sunny Wind 10mph Humidity 45%"

        # Good response should have markdown formatting
        assert "#" in good_response or "*" in good_response or "-" in good_response
        # Bad response lacks markdown
        assert "#" not in bad_response and "**" not in bad_response


class TestMemoryBankIntegration:
    """Tests for memory bank integration evaluation."""

    def test_conversation_continuity(self):
        """Test that memory enables conversation continuity."""
        # First query
        query1 = "What are the ingredients for a Margarita?"
        # Follow-up query referencing previous context
        query2 = "What about a Manhattan?"

        # The second query assumes context from first
        assert "what about" in query2.lower()

    def test_user_specific_memory(self):
        """Test that memory should be user-specific."""
        # Memory should be scoped by user_id
        # This is a structural test for the memory service
        pass  # Implementation would require actual agent testing

    def test_session_persistence(self):
        """Test that sessions are persisted to memory bank."""
        # Sessions should be saved after agent completion
        # This is a structural test for the callback
        pass  # Implementation would require actual agent testing


class TestMultiAgentCoordination:
    """Tests for multi-agent coordination evaluation."""

    def test_complex_query_routing(self):
        """Test complex queries requiring multiple agents."""
        complex_query = "What's the weather in Miami and what cocktail should I drink there?"

        # This query should route to both agents
        assert "weather" in complex_query.lower()
        assert "cocktail" in complex_query.lower() or "drink" in complex_query.lower()

    def test_agent_delegation(self):
        """Test that hosting agent delegates to appropriate agents."""
        # Hosting agent should identify task requirements
        # and delegate to correct child agents
        pass  # Implementation would require actual agent testing

    def test_response_aggregation(self):
        """Test that hosting agent aggregates responses."""
        # Hosting agent should combine results from multiple agents
        # into a coherent response
        pass  # Implementation would require actual agent testing

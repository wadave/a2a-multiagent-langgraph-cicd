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
"""Unit tests for agent cards."""

import pytest
from a2a.types import AgentCard, AgentSkill

# Import agent cards
from a2a_agents.cocktail_agent.cocktail_agent_card import (
    cocktail_agent_card,
    cocktail_agent_skill,
)
from a2a_agents.hosting_agent.hosting_agent_card import (
    hosting_agent_card,
    hosting_agent_skill,
)
from a2a_agents.weather_agent.weather_agent_card import (
    weather_agent_card,
    weather_agent_skill,
)


class TestCocktailAgentCard:
    """Tests for Cocktail Agent card configuration."""

    def test_cocktail_skill_exists(self):
        """Verify cocktail skill is properly configured."""
        assert isinstance(cocktail_agent_skill, AgentSkill)
        assert cocktail_agent_skill.id == "cocktail_cocktail"
        assert cocktail_agent_skill.name == "Search cocktail information"
        assert "cocktail" in cocktail_agent_skill.tags
        assert "drink" in cocktail_agent_skill.tags

    def test_cocktail_skill_examples(self):
        """Verify cocktail skill has proper examples."""
        assert len(cocktail_agent_skill.examples) >= 3
        assert any("Margarita" in example for example in cocktail_agent_skill.examples)
        assert any("random" in example.lower() for example in cocktail_agent_skill.examples)

    def test_cocktail_agent_card_structure(self):
        """Verify cocktail agent card is properly structured."""
        assert isinstance(cocktail_agent_card, AgentCard)
        assert cocktail_agent_card.name == "Cocktail Agent adk-mb - ADK"
        assert len(cocktail_agent_card.skills) == 1
        assert cocktail_agent_card.skills[0] == cocktail_agent_skill

    def test_cocktail_agent_card_naming(self):
        """Verify cocktail agent uses adk-mb naming convention."""
        assert "adk-mb" in cocktail_agent_card.name
        assert "ADK" in cocktail_agent_card.name


class TestWeatherAgentCard:
    """Tests for Weather Agent card configuration."""

    def test_weather_skill_exists(self):
        """Verify weather skill is properly configured."""
        assert isinstance(weather_agent_skill, AgentSkill)
        assert weather_agent_skill.id == "weather_search"
        assert weather_agent_skill.name == "Search weather"
        assert "weather" in weather_agent_skill.tags

    def test_weather_skill_examples(self):
        """Verify weather skill has proper examples."""
        assert len(weather_agent_skill.examples) >= 1
        examples_str = " ".join(weather_agent_skill.examples).lower()
        assert "weather" in examples_str

    def test_weather_agent_card_structure(self):
        """Verify weather agent card is properly structured."""
        assert isinstance(weather_agent_card, AgentCard)
        assert weather_agent_card.name == "Weather Agent adk-mb - ADK"
        assert len(weather_agent_card.skills) == 1
        assert weather_agent_card.skills[0] == weather_agent_skill

    def test_weather_agent_card_naming(self):
        """Verify weather agent uses adk-mb naming convention."""
        assert "adk-mb" in weather_agent_card.name
        assert "ADK" in weather_agent_card.name


class TestHostingAgentCard:
    """Tests for Hosting Agent card configuration."""

    def test_hosting_skill_exists(self):
        """Verify hosting skill is properly configured."""
        assert isinstance(hosting_agent_skill, AgentSkill)
        assert hosting_agent_skill.id == "hosting_agent"
        assert hosting_agent_skill.name == "Search hosting agent"
        assert "host_agent" in hosting_agent_skill.tags

    def test_hosting_skill_examples(self):
        """Verify hosting skill has comprehensive examples."""
        assert len(hosting_agent_skill.examples) >= 3
        examples_str = " ".join(hosting_agent_skill.examples).lower()
        assert "weather" in examples_str
        assert "cocktail" in examples_str or "margarita" in examples_str

    def test_hosting_agent_card_structure(self):
        """Verify hosting agent card is properly structured."""
        assert isinstance(hosting_agent_card, AgentCard)
        assert hosting_agent_card.name == "Hosting Agent adk-mb - ADK"
        assert len(hosting_agent_card.skills) == 1
        assert hosting_agent_card.skills[0] == hosting_agent_skill

    def test_hosting_agent_card_naming(self):
        """Verify hosting agent uses adk-mb naming convention."""
        assert "adk-mb" in hosting_agent_card.name
        assert "ADK" in hosting_agent_card.name

    def test_hosting_agent_description(self):
        """Verify hosting agent description mentions capabilities."""
        description = hosting_agent_skill.description
        assert "weather" in description.lower() or "cocktail" in description.lower()


class TestAgentCardConsistency:
    """Tests for consistency across all agent cards."""

    def test_all_cards_use_adk_mb_naming(self):
        """Verify all agents use consistent adk-mb naming."""
        cards = [cocktail_agent_card, weather_agent_card, hosting_agent_card]
        for card in cards:
            assert "adk-mb" in card.name
            assert "ADK" in card.name

    def test_all_skills_have_examples(self):
        """Verify all skills provide examples."""
        skills = [cocktail_agent_skill, weather_agent_skill, hosting_agent_skill]
        for skill in skills:
            assert len(skill.examples) > 0

    def test_all_skills_have_tags(self):
        """Verify all skills have tags."""
        skills = [cocktail_agent_skill, weather_agent_skill, hosting_agent_skill]
        for skill in skills:
            assert len(skill.tags) > 0

    def test_all_cards_have_descriptions(self):
        """Verify all agent cards have descriptions."""
        cards = [cocktail_agent_card, weather_agent_card, hosting_agent_card]
        for card in cards:
            assert card.description is not None
            assert len(card.description) > 0

    def test_skill_ids_are_unique(self):
        """Verify skill IDs are unique across all agents."""
        skills = [cocktail_agent_skill, weather_agent_skill, hosting_agent_skill]
        skill_ids = [skill.id for skill in skills]
        assert len(skill_ids) == len(set(skill_ids)), "Skill IDs must be unique"

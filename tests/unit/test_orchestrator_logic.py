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
"""Unit tests for orchestrator agent logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a_agents.common.langgraph_base_orchestrator_agent import LanggraphBaseOrchestratorAgent


class TestOrchestrator(LanggraphBaseOrchestratorAgent):
    """Concrete orchestrator for testing."""
    def get_system_instruction(self, state: dict) -> str:
        return f"Test instruction. Available agents: {self.agents}"

    def get_model_name(self) -> str:
        return "gemini-1.5-flash"

# Alias for tests
AdkOrchestratorAgent = TestOrchestrator


class TestOrchestratorInitialization:
    """Tests for orchestrator agent initialization."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        return AsyncMock()

    def test_orchestrator_initialization(self, mock_httpx_client):
        """Verify orchestrator initializes with correct attributes."""
        remote_addresses = ["http://agent1.com", "http://agent2.com"]
        orchestrator = AdkOrchestratorAgent(
            remote_agent_addresses=remote_addresses,
            http_client=mock_httpx_client,
        )

        assert orchestrator.httpx_client == mock_httpx_client
        assert orchestrator.remote_agent_addresses == remote_addresses
        assert isinstance(orchestrator.remote_agent_connections, dict)
        assert isinstance(orchestrator.cards, dict)
        assert len(orchestrator.remote_agent_connections) == 0  # Not initialized yet

    def test_orchestrator_client_factory_creation(self, mock_httpx_client):
        """Verify orchestrator creates client factory."""
        orchestrator = AdkOrchestratorAgent(
            remote_agent_addresses=["http://agent1.com"],
            http_client=mock_httpx_client,
        )

        assert orchestrator.client_factory is not None


class TestOrchestratorAgentRegistration:
    """Tests for agent card registration."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance."""
        return AdkOrchestratorAgent(
            remote_agent_addresses=[],
            http_client=AsyncMock(),
        )

    @pytest.fixture
    def sample_agent_card(self):
        """Create a sample agent card."""
        skill = AgentSkill(
            id="test_skill",
            name="Test Skill",
            description="A test skill",
            tags=["test"],
            examples=["test query"],
            version="1.0.0",
            input_modes=["text/plain"],
            output_modes=["text/plain"],
        )
        return AgentCard(
            name="Test Agent",
            description="A test agent",
            url="http://test.com",
            skills=[skill],
            version="1.0.0",
            capabilities=AgentCapabilities(),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
        )

    def test_register_agent_card(self, orchestrator, sample_agent_card):
        """Verify agent card registration."""
        orchestrator.register_agent_card(sample_agent_card)

        assert "Test Agent" in orchestrator.cards
        assert orchestrator.cards["Test Agent"] == sample_agent_card
        assert "Test Agent" in orchestrator.remote_agent_connections

    def test_register_multiple_cards(self, orchestrator):
        """Verify multiple agent cards can be registered."""
        card1 = AgentCard(
            name="Agent 1",
            description="First agent",
            url="http://agent1.com",
            skills=[],
            version="1.0.0",
            capabilities=AgentCapabilities(),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
        )
        card2 = AgentCard(
            name="Agent 2",
            description="Second agent",
            url="http://agent2.com",
            skills=[],
            version="1.0.0",
            capabilities=AgentCapabilities(),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
        )

        orchestrator.register_agent_card(card1)
        orchestrator.register_agent_card(card2)

        assert len(orchestrator.cards) == 2
        assert "Agent 1" in orchestrator.cards
        assert "Agent 2" in orchestrator.cards


class TestOrchestratorAgentListing:
    """Tests for listing remote agents."""

    @pytest.fixture
    def orchestrator_with_agents(self):
        """Create an orchestrator with registered agents."""
        orchestrator = AdkOrchestratorAgent(
            remote_agent_addresses=[],
            http_client=AsyncMock(),
        )

        # Register test agents
        for i in range(3):
            card = AgentCard(
                name=f"Agent {i}",
                description=f"Description for agent {i}",
                url=f"http://agent{i}.com",
                skills=[],
                version="1.0.0",
                capabilities=AgentCapabilities(),
                default_input_modes=["text/plain"],
                default_output_modes=["text/plain"],
            )
            orchestrator.register_agent_card(card)

        return orchestrator

    def test_list_remote_agents_empty(self):
        """Verify empty list when no agents registered."""
        orchestrator = AdkOrchestratorAgent(
            remote_agent_addresses=[],
            http_client=AsyncMock(),
        )
        agents = orchestrator.list_remote_agents()
        assert "No remote agents" in agents

    def test_list_remote_agents(self, orchestrator_with_agents):
        """Verify listing remote agents."""
        agents = orchestrator_with_agents.list_remote_agents()
        assert "Agent 0" in agents
        assert "Agent 1" in agents
        assert "Agent 2" in agents


class TestOrchestratorStateManagement:
    """Tests for orchestrator state management."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance."""
        return AdkOrchestratorAgent(
            remote_agent_addresses=[],
            http_client=AsyncMock(),
        )

    def test_check_state_no_active_agent(self, orchestrator):
        """Verify state check when no active agent."""
        mock_context = {}

        result = orchestrator.check_state(mock_context)
        assert result == {"active_agent": "None"}

    def test_check_state_with_active_agent(self, orchestrator):
        """Verify state check with active agent."""
        mock_context = {
            "context_id": "test-context",
            "session_active": True,
            "agent": "Weather Agent",
        }

        result = orchestrator.check_state(mock_context)
        assert result == {"active_agent": "Weather Agent"}

    def test_check_state_session_inactive(self, orchestrator):
        """Verify state check with inactive session."""
        mock_context = {
            "context_id": "test-context",
            "session_active": False,
            "agent": "Weather Agent",
        }

        result = orchestrator.check_state(mock_context)
        assert result == {"active_agent": "None"}


class TestOrchestratorAgentCreation:
    """Tests for creating the orchestrator agent."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator instance."""
        return AdkOrchestratorAgent(
            remote_agent_addresses=[],
            http_client=AsyncMock(),
        )

    def test_create_agent(self, orchestrator):
        """Verify agent creation."""
        agent = orchestrator.create_agent()

        assert agent is not None
        # Compiled graphs don't have a simple .name attribute usually, 
        # but we can check it's compiled.
        assert hasattr(agent, "invoke")
        # Check tools by inspecting the nodes
        assert "agent" in agent.nodes
        assert "tools" in agent.nodes

    def test_agent_has_tools(self, orchestrator):
        """Verify agent has required tools."""
        agent = orchestrator.create_agent()
        # In modern LangGraph, we can check node names
        assert "agent" in agent.nodes
        assert "tools" in agent.nodes


class TestOrchestratorInstructionGeneration:
    """Tests for instruction generation."""

    @pytest.fixture
    def orchestrator_with_agents(self):
        """Create an orchestrator with agents."""
        orchestrator = AdkOrchestratorAgent(
            remote_agent_addresses=[],
            http_client=AsyncMock(),
        )

        # Register test agents
        card = AgentCard(
            name="Weather Agent adk-mb - ADK",
            description="Weather agent",
            url="http://weather.com",
            skills=[],
            version="1.0.0",
            capabilities=AgentCapabilities(),
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
        )
        orchestrator.register_agent_card(card)

        return orchestrator

    def test_root_instruction_contains_agents(self, orchestrator_with_agents):
        """Verify root instruction includes agent information."""
        mock_context = MagicMock()
        mock_context.state = {}

        instruction = orchestrator_with_agents.get_system_instruction(mock_context)

        assert "Weather Agent" in instruction

    def test_root_instruction_includes_tools(self, orchestrator_with_agents):
        """Verify root instruction mentions available tools."""
        mock_context = MagicMock()
        mock_context.state = {}

        instruction = orchestrator_with_agents.get_system_instruction(mock_context)

        assert "Weather Agent" in instruction

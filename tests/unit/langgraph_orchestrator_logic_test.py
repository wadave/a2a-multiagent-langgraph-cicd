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
"""Unit tests for LanggraphBaseOrchestratorAgent retrieve_card and init logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from a2a.types import AgentCapabilities, AgentCard

from a2a_agents.common.langgraph_base_orchestrator_agent import (
    LanggraphBaseOrchestratorAgent,
)


# Concrete subclass for testing the abstract base class
class _TestOrchestrator(LanggraphBaseOrchestratorAgent):
    def get_system_instruction(self, state: dict) -> str:
        return "test instruction"


def _make_orchestrator(addresses=None):
    """Create a test orchestrator instance."""
    return _TestOrchestrator(
        remote_agent_addresses=addresses or [],
        http_client=AsyncMock(),
    )


def _make_agent_card(name="Test Agent"):
    """Create a minimal AgentCard for testing."""
    return AgentCard(
        name=name,
        description=f"{name} description",
        url="http://test.com",
        version="1.0",
        skills=[],
        capabilities=AgentCapabilities(),
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
    )


# ---------------------------------------------------------------------------
# Card path selection
# ---------------------------------------------------------------------------


class TestRetrieveCardPathSelection:
    """Tests for correct agent_card_path based on URL type."""

    @pytest.mark.asyncio
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_reasoning_engine_url_uses_a2a_path(self, mock_resolver_cls):
        """Reasoning Engine URLs should use 'a2a/v1/card' path."""
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.return_value = _make_agent_card()
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        address = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/123/locations/us-central1/reasoningEngines/456"

        await orchestrator.retrieve_card(address)

        mock_resolver_cls.assert_called_once_with(
            orchestrator.httpx_client,
            base_url=address,
            agent_card_path="a2a/v1/card",
        )

    @pytest.mark.asyncio
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_non_reasoning_engine_url_uses_default_path(self, mock_resolver_cls):
        """Non-RE URLs should use 'v1/card' path."""
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.return_value = _make_agent_card()
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        address = "http://localhost:10001"

        await orchestrator.retrieve_card(address)

        mock_resolver_cls.assert_called_once_with(
            orchestrator.httpx_client,
            base_url=address,
            agent_card_path="v1/card",
        )

    @pytest.mark.asyncio
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_trailing_slash_stripped(self, mock_resolver_cls):
        """Trailing slashes should be stripped from the address."""
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.return_value = _make_agent_card()
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001/")

        mock_resolver_cls.assert_called_once_with(
            orchestrator.httpx_client,
            base_url="http://localhost:10001",
            agent_card_path="v1/card",
        )

    @pytest.mark.asyncio
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_card_registered_on_success(self, mock_resolver_cls):
        """A successful fetch should register the card."""
        card = _make_agent_card("My Agent")
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.return_value = card
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001")

        assert "My Agent" in orchestrator.cards
        assert "My Agent" in orchestrator.remote_agent_connections


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


class TestRetrieveCardRetryLogic:
    """Tests for retry behavior on transient vs non-transient errors."""

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_retries_on_connect_error(self, mock_resolver_cls, mock_sleep):
        """ConnectError should trigger retries with backoff."""
        card = _make_agent_card()
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = [
            httpx.ConnectError("connection refused"),
            card,
        ]
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001")

        assert mock_resolver.get_agent_card.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2**0 = 1
        assert "Test Agent" in orchestrator.cards

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_retries_on_timeout(self, mock_resolver_cls, mock_sleep):
        """TimeoutException should trigger retries."""
        card = _make_agent_card()
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = [
            httpx.TimeoutException("timed out"),
            httpx.TimeoutException("timed out again"),
            card,
        ]
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001")

        assert mock_resolver.get_agent_card.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # 2**0
        mock_sleep.assert_any_call(2)  # 2**1
        assert "Test Agent" in orchestrator.cards

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_retries_on_5xx_error(self, mock_resolver_cls, mock_sleep):
        """5xx HTTPStatusError should trigger retries."""
        card = _make_agent_card()
        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = [
            httpx.HTTPStatusError("503", request=MagicMock(), response=mock_response),
            card,
        ]
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001")

        assert mock_resolver.get_agent_card.call_count == 2
        assert "Test Agent" in orchestrator.cards

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_no_retry_on_4xx_error(self, mock_resolver_cls, mock_sleep):
        """4xx HTTPStatusError should fail immediately without retrying."""
        mock_response = MagicMock()
        mock_response.status_code = 400

        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=mock_response
        )
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001")

        assert mock_resolver.get_agent_card.call_count == 1
        mock_sleep.assert_not_called()
        assert len(orchestrator.cards) == 0

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_no_retry_on_unknown_exception(self, mock_resolver_cls, mock_sleep):
        """Unexpected exceptions should fail immediately without retrying."""
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = ValueError("something unexpected")
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001")

        assert mock_resolver.get_agent_card.call_count == 1
        mock_sleep.assert_not_called()
        assert len(orchestrator.cards) == 0

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_all_retries_exhausted(self, mock_resolver_cls, mock_sleep):
        """When all retries fail, card should not be registered."""
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = httpx.ConnectError("refused")
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.retrieve_card("http://localhost:10001", max_retries=3)

        assert mock_resolver.get_agent_card.call_count == 3
        assert mock_sleep.call_count == 2  # No sleep after last attempt
        assert len(orchestrator.cards) == 0


# ---------------------------------------------------------------------------
# Graceful degradation (init_remote_agent_addresses)
# ---------------------------------------------------------------------------


class TestInitRemoteAgentAddresses:
    """Tests for init_remote_agent_addresses resilience."""

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_all_agents_loaded(self, mock_resolver_cls, mock_sleep):
        """All agents load successfully."""
        cards = [_make_agent_card("Agent1"), _make_agent_card("Agent2")]
        call_count = 0

        async def get_card_side_effect():
            nonlocal call_count
            card = cards[call_count]
            call_count += 1
            return card

        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = get_card_side_effect
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.init_remote_agent_addresses(
            [
                "http://agent1.com",
                "http://agent2.com",
            ]
        )

        assert orchestrator._cards_loaded is True
        assert len(orchestrator.cards) == 2
        assert "Agent1" in orchestrator.cards
        assert "Agent2" in orchestrator.cards

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_partial_failure_does_not_crash(self, mock_resolver_cls, mock_sleep):
        """One agent failing should not prevent others from loading."""
        card = _make_agent_card("GoodAgent")
        mock_response = MagicMock()
        mock_response.status_code = 400

        call_count = 0

        async def get_card_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                # First resolver fails with 400 (non-retryable)
                raise httpx.HTTPStatusError("400", request=MagicMock(), response=mock_response)
            return card

        # Both addresses share the same resolver mock, but we need separate
        # resolver instances per address. Use side_effect on the class.
        resolvers = []

        def make_resolver(*args, **kwargs):
            r = AsyncMock()
            r.get_agent_card.side_effect = get_card_side_effect
            resolvers.append(r)
            return r

        mock_resolver_cls.side_effect = make_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.init_remote_agent_addresses(
            [
                "http://bad-agent.com",
                "http://good-agent.com",
            ]
        )

        assert orchestrator._cards_loaded is True
        assert len(orchestrator.cards) == 1
        assert "GoodAgent" in orchestrator.cards

    @pytest.mark.asyncio
    @patch(
        "a2a_agents.common.langgraph_base_orchestrator_agent.asyncio.sleep", new_callable=AsyncMock
    )
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_all_agents_fail(self, mock_resolver_cls, mock_sleep):
        """All agents failing should still set _cards_loaded and not raise."""
        mock_resolver = AsyncMock()
        mock_resolver.get_agent_card.side_effect = httpx.ConnectError("refused")
        mock_resolver_cls.return_value = mock_resolver

        orchestrator = _make_orchestrator()
        await orchestrator.init_remote_agent_addresses(
            [
                "http://agent1.com",
                "http://agent2.com",
            ]
        )

        assert orchestrator._cards_loaded is True
        assert len(orchestrator.cards) == 0

    @pytest.mark.asyncio
    @patch("a2a_agents.common.langgraph_base_orchestrator_agent.A2ACardResolver")
    async def test_empty_address_list(self, mock_resolver_cls):
        """Empty address list should succeed with no cards."""
        orchestrator = _make_orchestrator()
        await orchestrator.init_remote_agent_addresses([])

        assert orchestrator._cards_loaded is True
        assert len(orchestrator.cards) == 0
        mock_resolver_cls.assert_not_called()

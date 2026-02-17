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
"""Unit tests for frontend logic."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGoogleAuthClass:
    """Tests for GoogleAuth authentication class."""

    @patch("frontend.main.default")
    def test_google_auth_initialization(self, mock_default):
        """Verify GoogleAuth initializes with credentials."""
        mock_credentials = MagicMock()
        mock_default.return_value = (mock_credentials, "test-project")

        # Import here to use the mocked default
        from frontend.main import GoogleAuth

        auth = GoogleAuth()

        assert auth.credentials == mock_credentials
        assert auth.project == "test-project"
        mock_default.assert_called_once_with(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

    @patch("frontend.main.default")
    def test_google_auth_flow_refreshes_credentials(self, mock_default):
        """Verify auth flow refreshes expired credentials."""
        mock_credentials = MagicMock()
        mock_credentials.valid = False
        mock_credentials.token = "test-token"
        mock_default.return_value = (mock_credentials, "test-project")

        from frontend.main import GoogleAuth

        auth = GoogleAuth()
        mock_request = MagicMock()

        # Execute auth flow
        flow = auth.auth_flow(mock_request)
        next(flow)

        # Verify credentials were refreshed
        mock_credentials.refresh.assert_called_once()
        assert mock_request.headers["Authorization"] == "Bearer test-token"

    @patch("frontend.main.default")
    def test_google_auth_flow_uses_valid_credentials(self, mock_default):
        """Verify auth flow uses valid credentials without refresh."""
        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "test-token"
        mock_default.return_value = (mock_credentials, "test-project")

        from frontend.main import GoogleAuth

        auth = GoogleAuth()
        mock_request = MagicMock()

        # Execute auth flow
        flow = auth.auth_flow(mock_request)
        next(flow)

        # Verify credentials were NOT refreshed
        mock_credentials.refresh.assert_not_called()
        assert mock_request.headers["Authorization"] == "Bearer test-token"


class TestEnvironmentConfiguration:
    """Tests for environment variable configuration."""

    @patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "PROJECT_NUMBER": "123456",
        "AGENT_ENGINE_ID": "789",
        "GOOGLE_CLOUD_LOCATION": "us-west1"
    })
    def test_environment_variables_loaded(self):
        """Verify environment variables are loaded correctly."""
        # Force reload of main module to pick up environment
        import importlib
        import frontend.main
        importlib.reload(frontend.main)

        assert frontend.main.PROJECT_ID == "test-project"
        assert frontend.main.PROJECT_NUMBER == "123456"
        assert frontend.main.AGENT_ENGINE_ID == "789"
        assert frontend.main.LOCATION == "us-west1"

    @patch.dict(os.environ, {"GOOGLE_CLOUD_LOCATION": ""}, clear=True)
    def test_default_location_used(self):
        """Verify default location is used when not specified."""
        import importlib
        import frontend.main
        importlib.reload(frontend.main)

        # Default should be us-central1
        assert frontend.main.LOCATION == "us-central1"


class TestAgentCardRetrieval:
    """Tests for agent card retrieval."""

    @pytest.mark.asyncio
    @patch("frontend.main.client")
    async def test_get_agent_card_success(self, mock_client):
        """Verify successful agent card retrieval."""
        mock_agent = AsyncMock()
        mock_card = MagicMock()
        mock_card.name = "Test Agent"
        mock_agent.handle_authenticated_agent_card.return_value = mock_card

        mock_client.agent_engines.get.return_value = mock_agent

        from frontend.main import get_agent_card

        resource_name = "projects/123/locations/us-central1/reasoningEngines/789"
        result = await get_agent_card(resource_name)

        assert result == mock_card
        mock_client.agent_engines.get.assert_called_once()
        mock_agent.handle_authenticated_agent_card.assert_awaited_once()


class TestResponseProcessing:
    """Tests for response processing from agents."""

    def test_task_state_enum_values(self):
        """Verify TaskState enum has expected values."""
        from a2a.types import TaskState

        assert hasattr(TaskState, "completed")
        assert hasattr(TaskState, "failed")

    @pytest.mark.asyncio
    async def test_message_creation(self):
        """Verify message creation with proper structure."""
        from a2a.types import Message, Part, Role, TextPart

        message = Message(
            message_id="test-123",
            role=Role.user,
            parts=[Part(root=TextPart(text="test query"))],
        )

        assert message.message_id == "test-123"
        assert message.role == Role.user
        assert len(message.parts) == 1
        assert message.parts[0].root.text == "test query"


class TestErrorHandling:
    """Tests for error handling in frontend."""

    @pytest.mark.asyncio
    @patch("frontend.main.get_agent_card")
    @patch("frontend.main.httpx.AsyncClient")
    async def test_error_handling_in_get_response(self, mock_client_class, mock_get_card):
        """Verify error handling in get_response_from_agent."""
        # Mock agent card retrieval to raise an exception
        mock_get_card.side_effect = Exception("Test error")

        from frontend.main import get_response_from_agent

        # Execute the function
        result_generator = get_response_from_agent("test query", [])
        messages = []
        async for msg in result_generator:
            messages.append(msg)

        # Should yield error message
        assert len(messages) > 0
        assert "error" in messages[0].content.lower()


class TestResourceNameConstruction:
    """Tests for resource name construction."""

    @patch.dict(os.environ, {
        "PROJECT_NUMBER": "123456",
        "GOOGLE_CLOUD_LOCATION": "us-central1",
        "AGENT_ENGINE_ID": "789"
    })
    def test_resource_name_format(self):
        """Verify resource name is properly formatted."""
        import importlib
        import frontend.main
        importlib.reload(frontend.main)

        expected = "projects/123456/locations/us-central1/reasoningEngines/789"
        assert frontend.main.remote_a2a_agent_resource_name == expected

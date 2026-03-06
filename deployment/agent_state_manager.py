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
import json
import logging
import os
import subprocess
from datetime import UTC, datetime


class AgentStateManager:
    """Manages persistent state for deployed agents in GCS."""

    def __init__(self, project_id: str, environment: str, region: str = "us-central1"):
        self.project_id = project_id
        self.environment = environment
        self.region = region
        self.bucket_name = f"{project_id}-terraform-state"
        self.state_path = f"a2a-multiagent-langgraph-cicd/{environment}/agent_state.json"
        self.gcs_uri = f"gs://{self.bucket_name}/{self.state_path}"

    def read_state(self) -> dict | None:
        """Read agent state from GCS. Returns None if not found."""
        try:
            result = subprocess.run(
                ["gcloud", "storage", "cat", self.gcs_uri],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                state = json.loads(result.stdout)
                self._validate_state_schema(state)
                logging.info(f"Successfully read state from {self.gcs_uri}")
                return state
            else:
                logging.warning(f"State file not found at {self.gcs_uri}")
                return None
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in state file: {e}")
            raise
        except Exception as e:
            logging.error(f"Failed to read state: {e}")
            raise

    def write_state(self, state: dict) -> None:
        """Write agent state to GCS."""
        self._validate_state_schema(state)
        state["last_updated"] = datetime.now(UTC).isoformat()

        # Write to temp file then upload
        temp_file = "/tmp/agent_state.json"
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)

        try:
            subprocess.run(
                ["gcloud", "storage", "cp", temp_file, self.gcs_uri],
                check=True,
                capture_output=True,
            )
            logging.info(f"Successfully wrote state to {self.gcs_uri}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to write state: {e.stderr.decode()}")
            raise

    def update_agent(self, agent_type: str, resource_name: str, commit_sha: str = None) -> None:
        """Update a single agent's state."""
        state = self.read_state() or self._create_empty_state()

        state["agents"][agent_type] = {
            "resource_name": resource_name,
            "deployed_at": datetime.now(UTC).isoformat(),
            "deployed_by_commit": commit_sha or os.getenv("GITHUB_SHA", "unknown"),
        }

        self.write_state(state)

    def get_agent_id(self, agent_type: str) -> str | None:
        """Get the full resource name for an agent. Returns None if not found."""
        state = self.read_state()
        if state and agent_type in state.get("agents", {}):
            return state["agents"][agent_type]["resource_name"]
        return None

    def _create_empty_state(self) -> dict:
        """Create empty state structure."""
        return {
            "version": "1.0",
            "environment": self.environment,
            "project_id": self.project_id,
            "project_number": os.getenv("PROJECT_NUMBER", ""),
            "agents": {},
        }

    def _validate_state_schema(self, state: dict) -> None:
        """Validate state file has required fields."""
        required_fields = ["version", "environment", "project_id", "agents"]
        for field in required_fields:
            if field not in state:
                raise ValueError(f"State file missing required field: {field}")

        if not isinstance(state["agents"], dict):
            raise ValueError("State field 'agents' must be a dictionary")

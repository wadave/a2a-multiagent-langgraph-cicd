import json
import logging
import subprocess
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Optional

class AgentStateManager:
    """Manages persistent state for deployed agents in GCS."""

    def __init__(self, project_id: str, environment: str, region: str = "us-central1"):
        self.project_id = project_id
        self.environment = environment
        self.region = region
        self.bucket_name = f"{project_id}-terraform-state"
        self.state_path = f"a2a-multiagent-langgraph-cicd/{environment}/agent_state.json"
        self.gcs_uri = f"gs://{self.bucket_name}/{self.state_path}"

    def read_state(self) -> Optional[Dict]:
        """Read agent state from GCS. Returns None if not found."""
        try:
            result = subprocess.run(
                ["gcloud", "storage", "cat", self.gcs_uri],
                capture_output=True,
                text=True,
                check=False
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

    def write_state(self, state: Dict) -> None:
        """Write agent state to GCS."""
        self._validate_state_schema(state)
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Write to temp file then upload
        temp_file = "/tmp/agent_state.json"
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)

        try:
            subprocess.run(
                ["gcloud", "storage", "cp", temp_file, self.gcs_uri],
                check=True,
                capture_output=True
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
            "deployed_at": datetime.now(timezone.utc).isoformat(),
            "deployed_by_commit": commit_sha or os.getenv("GITHUB_SHA", "unknown")
        }

        self.write_state(state)

    def get_agent_id(self, agent_type: str) -> Optional[str]:
        """Get the full resource name for an agent. Returns None if not found."""
        state = self.read_state()
        if state and agent_type in state.get("agents", {}):
            return state["agents"][agent_type]["resource_name"]
        return None

    def _create_empty_state(self) -> Dict:
        """Create empty state structure."""
        return {
            "version": "1.0",
            "environment": self.environment,
            "project_id": self.project_id,
            "project_number": os.getenv("PROJECT_NUMBER", ""),
            "agents": {}
        }

    def _validate_state_schema(self, state: Dict) -> None:
        """Validate state file has required fields."""
        required_fields = ["version", "environment", "project_id", "agents"]
        for field in required_fields:
            if field not in state:
                raise ValueError(f"State file missing required field: {field}")

        if not isinstance(state["agents"], dict):
            raise ValueError("State field 'agents' must be a dictionary")

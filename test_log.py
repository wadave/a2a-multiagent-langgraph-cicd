import logging
import os
import sys

# Add src to path
sys.path.append('src')

from a2a_agents.common.logging_utils import setup_cloud_logging

# Mock the cloud logging import to test fallback
os.environ["USE_CLOUD_LOGGING"] = "TRUE"
setup_cloud_logging()
setup_cloud_logging()

logging.info("Test message")

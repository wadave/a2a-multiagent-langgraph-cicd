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

import logging
import os

_cloud_logging_initialized = False

def setup_cloud_logging(log_name: str = "a2a-agent", level=logging.INFO):
    """Sets up Google Cloud Logging if running in a supported environment.
    
    This function initializes the Google Cloud Logging client and sets it up
    to be the handler for all standard logging calls.
    
    Args:
        log_name: The name of the log to write to.
        level: The logging level to use (default: logging.INFO)
    """
    global _cloud_logging_initialized
    if _cloud_logging_initialized:
        return
        
    # Detect if we should use Cloud Logging. 
    # Usually enabled if running on GCP (Cloud Run, Vertex AI) or explicitly requested.
    use_cloud_logging = os.getenv("USE_CLOUD_LOGGING", "TRUE").lower() in ["true", "1"]
    
    if use_cloud_logging:
        try:
            import google.cloud.logging
            
            client = google.cloud.logging.Client()
            client.setup_logging(log_level=level)
            _cloud_logging_initialized = True
            logging.info(f"Google Cloud Logging initialized for: {log_name}")
            
        except ImportError:
            logging.basicConfig(level=level)
            _cloud_logging_initialized = True
            logging.warning("google-cloud-logging not installed. Falling back to standard logging.")
        except Exception as e:
            logging.basicConfig(level=level)
            _cloud_logging_initialized = True
            logging.warning(f"Failed to initialize Google Cloud Logging: {e}. Falling back to standard logging.")
    else:
        logging.basicConfig(level=level)
        _cloud_logging_initialized = True
        logging.info("Cloud Logging disabled. Using standard logging.")

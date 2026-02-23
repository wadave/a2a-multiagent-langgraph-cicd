# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Enable the Identity and Access Management API
resource "google_project_service" "iam_manager_api" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

# Enable the Service Usage API
resource "google_project_service" "serviceusage_api" {
  service            = "serviceusage.googleapis.com"
  disable_on_destroy = false
}

# Enable the Service Management API
resource "google_project_service" "servicemanagement_api" {
  service            = "servicemanagement.googleapis.com"
  disable_on_destroy = false
}

# Enable the Vertex AI API
resource "google_project_service" "vertex_ai_api" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Enable the Discovery Engine API
resource "google_project_service" "discovery_engine_api" {
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false
}

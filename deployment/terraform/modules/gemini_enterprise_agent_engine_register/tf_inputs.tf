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

variable "project_id" {
  description = "The GCP project name."
  type        = string
}

variable "agent_engine_region" {
  description = "The GCP Agent Engine region."
  type        = string
}

variable "gemini_enterprise_region" {
  description = "The GCP Gemini Enterprise region."
  type        = string
}

variable "gemini_enterprise_agent_name" {
  description = "The gemini_enterprise agent display name."
  type        = string
}

variable "gemini_enterprise_tool_description" {
  description = "The agent gemini_enterprise tool description."
  type        = string
}

variable "agent_display_name" {
  description = "The agent engine resource display name."
  type        = string
}

variable "agent_description" {
  description = "The agent engine resource description."
  type        = string
}

variable "collection_id" {
  default     = "default_collection"
  description = "The discovery engine collection ID."
  type        = string
}

variable "gemini_enterprise_app_id" {
  description = "The gemini_enterprise app resource ID."
  type        = string
}

variable "authorization_ids" {
  description = "The optional map of the Gemini Enterprise authorization ID where EnvVar=>AuthId."
  type        = map(string)
  default     = {}
}

variable "agent_engine_id" {
  description = "The agent engine resource name."
  type        = string
}

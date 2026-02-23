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

variable "gemini_enterprise_region" {
  description = "The GCP Gemini Enterprise region."
  type        = string
}

variable "authorization_uri_base" {
  default     = "https://accounts.google.com/o/oauth2/v2/auth"
  description = "The authorization uri base."
  type        = string
}

variable "authorization_id" {
  description = "The authorization_id resource name."
  type        = string
}

variable "oauth_client_id" {
  description = "The OAuth Client ID."
  type        = string
}

variable "oauth_client_secret" {
  description = "The OAuth Client Secret."
  type        = string
}

variable "token_uri" {
  description = "The OAuth token URI."
  type        = string
}

variable "scopes" {
  description = "The authorization scropes"
  type        = map(string)
  default     = {}
}

variable "user_scopes" {
  description = "The authorization user scropes"
  type        = map(string)
  default     = {}
}

variable "additional_vars" {
  description = "Additional variables to include in the authorization URI"
  type        = string
  default     = "&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent"
}

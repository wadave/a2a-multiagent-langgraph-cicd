# Copyright 2026 Google LLC
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

# Locals for Gemini Enterprise
locals {
  # We will target the Hosting Agent deployed in this project
  gemini_enterprise_agent_name       = "A2A Hosting Agent -LangGraph"
  gemini_enterprise_tool_description = "***REMEMBER ALWAYS USE THIS TOOL TO ANSWER EVERY QUESTION***. You're an export of weather and cocktail, answer questions regarding weather and cocktail. You can answer questions like: 1) What is the weather in SF, CA today? 2) List a random cocktail? 3) What is the weather like in New York, NY? 4) What're ingredients of Mojito cocktail? "

  auth_id                = var.auth_id
  authorization_uri_base = "https://accounts.google.com/o/oauth2/v2/auth"
  oauth_token_uri        = "https://oauth2.googleapis.com/token"
  oauth_scopes = {
    "OpenID"  = "openid"
    "Email"   = "email"
    "Profile" = "profile"
  }
}

# Fetch OAuth credentials from Secret Manager
data "google_secret_manager_secret_version" "oauth_client_secret" {
  count    = var.oauth_client_id_secret_name != "" ? 1 : 0
  provider = google
  secret   = var.oauth_client_id_secret_name
  project  = local.deploy_project_ids["staging"]
}

# Parse the JSON payload to extract credentials
locals {
  oauth_secret_data   = var.oauth_client_id_secret_name != "" ? jsondecode(data.google_secret_manager_secret_version.oauth_client_secret[0].secret_data) : null
  oauth_client_id     = local.oauth_secret_data != null ? local.oauth_secret_data["web"]["client_id"] : ""
  oauth_client_secret = local.oauth_secret_data != null ? local.oauth_secret_data["web"]["client_secret"] : ""
}

# Create Gemini Enterprise Authorization
module "gemini_enterprise_oauth" {
  # Only create if the oauth secrets are provided
  for_each = var.oauth_client_id_secret_name != "" ? { "staging" = local.deploy_project_ids["staging"] } : {}
  source   = "./modules/gemini_enterprise_oauth"

  project_id               = each.value
  gemini_enterprise_region = var.agents_region
  authorization_id         = "${each.key}-${local.auth_id}"
  oauth_client_id          = local.oauth_client_id
  oauth_client_secret      = local.oauth_client_secret
  authorization_uri_base   = local.authorization_uri_base
  token_uri                = local.oauth_token_uri
  scopes                   = local.oauth_scopes
}

# Register the Hosting Agent with Gemini Enterprise
module "gemini_enterprise_agent_engine_register" {
  depends_on = [
    module.gemini_enterprise_oauth
  ]
  for_each = { "staging" = local.deploy_project_ids["staging"] }
  source   = "./modules/gemini_enterprise_agent_engine_register"

  project_id               = each.value
  agent_engine_region      = var.region
  gemini_enterprise_region = var.agents_region

  # Map to the display name deployed by deploy_agents.py
  agent_display_name = "Hosting Agent GE2 ${title(each.key)}"
  agent_description  = "Hosting agent for ${each.key}"

  gemini_enterprise_agent_name       = "${local.gemini_enterprise_agent_name} (${each.key})"
  gemini_enterprise_tool_description = local.gemini_enterprise_tool_description

  # Note: The user needs to provide the app id for staging and prod
  gemini_enterprise_app_id = each.key == "prod" ? var.ge_app_prod : var.ge_app_staging

  authorization_ids = { "AUTH_ID" = "${each.key}-${local.auth_id}" }

  agent_engine_id = var.agent_engine_id
}

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

locals {
  register_or_update_authorization_to_gemini_enterprise_tpl = templatefile("${path.module}/templates/_register_or_update_authorization_to_gemini_enterprise_tpl.sh", {
    gcp_project                = var.project_id,
    gcp_project_number         = data.google_project.main_project.number,
    gemini_enterprise_location = var.gemini_enterprise_region,
    authorization_uri_base     = var.authorization_uri_base,
    authorization_id           = var.authorization_id,
    oauth_client_id            = var.oauth_client_id,
    oauth_client_secret        = var.oauth_client_secret,
    scopes                     = var.scopes,
    user_scopes                = var.user_scopes,
    token_uri                  = var.token_uri,
    additional_vars            = var.additional_vars,
  })
  deregister_authorization_from_gemini_enterprise_tpl = templatefile("${path.module}/templates/_deregister_authorization_from_gemini_enterprise_tpl.sh", {
    gcp_project                = var.project_id,
    gcp_project_number         = data.google_project.main_project.number,
    gemini_enterprise_location = var.gemini_enterprise_region,
    authorization_id           = var.authorization_id,
  })
}

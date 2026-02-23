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
  register_or_update_agent_engine_to_gemini_enterprise_tpl = templatefile("${path.module}/templates/_register_or_update_agent_engine_to_gemini_enterprise_tpl.sh", {
    gcp_project                        = var.project_id,
    gcp_project_number                 = data.google_project.main_project.number,
    agent_engine_location              = var.agent_engine_region,
    gemini_enterprise_location         = var.gemini_enterprise_region,
    agent_display_name                 = var.agent_display_name,
    agent_engine_id                    = var.agent_engine_id,
    gemini_enterprise_agent_name       = var.gemini_enterprise_agent_name,
    agent_description                  = var.agent_description,
    gemini_enterprise_tool_description = var.gemini_enterprise_tool_description,
    collection_id                      = var.collection_id,
    gemini_enterprise_app_id           = var.gemini_enterprise_app_id,
    authorization_ids                  = var.authorization_ids,
  })
  deregister_agent_engine_from_gemini_enterprise_tpl = templatefile("${path.module}/templates/_deregister_agent_engine_from_gemini_enterprise_tpl.sh", {
    gcp_project                  = var.project_id,
    agent_engine_location        = var.agent_engine_region,
    gemini_enterprise_location   = var.gemini_enterprise_region,
    agent_display_name           = var.agent_display_name,
    agent_engine_id              = var.agent_engine_id,
    gemini_enterprise_agent_name = var.gemini_enterprise_agent_name,
    agent_description            = var.agent_description,
    collection_id                = var.collection_id,
    gemini_enterprise_app_id     = var.gemini_enterprise_app_id,
  })
}

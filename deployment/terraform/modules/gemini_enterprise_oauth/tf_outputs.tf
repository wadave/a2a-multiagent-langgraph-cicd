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

# Create Module Build Directory if missing
resource "null_resource" "create_build_dir_if_missing" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/build"
  }
}

# Generate register_or_update_authorization_from_gemini_enterprise script
resource "local_file" "out_register_or_update_authorization_to_gemini_enterprise" {
  depends_on = [
    google_project_service.discovery_engine_api,
    google_project_service.vertex_ai_api,
    null_resource.create_build_dir_if_missing,
  ]
  content         = local.register_or_update_authorization_to_gemini_enterprise_tpl
  filename        = "${path.module}/build/_register_or_update_authorization_to_gemini_enterprise_tpl.sh"
  file_permission = "0755"
}

# Generate deregister_authorization_from_gemini_enterprise script
resource "local_file" "out_deregister_authorization_from_gemini_enterprise" {
  depends_on = [
    google_project_service.discovery_engine_api,
    google_project_service.vertex_ai_api,
    null_resource.create_build_dir_if_missing,
  ]
  content         = local.deregister_authorization_from_gemini_enterprise_tpl
  filename        = "${path.module}/build/_deregister_authorization_from_gemini_enterprise_tpl.sh"
  file_permission = "0755"
}

# Update authorization to Gemini Enterprise
resource "null_resource" "register_or_update_authorization_to_gemini_enterprise" {
  depends_on = [
    local_file.out_register_or_update_authorization_to_gemini_enterprise
  ]

  triggers = {
    scopes_trigger = jsonencode(var.scopes)
    template_hash  = md5(local.register_or_update_authorization_to_gemini_enterprise_tpl)
  }

  provisioner "local-exec" {
    command     = "./${path.module}/build/_register_or_update_authorization_to_gemini_enterprise_tpl.sh"
    interpreter = ["/bin/bash", "-c"]
  }
}

# Deregister authorization to Gemini Enterprise
resource "null_resource" "deregister_authorization_from_gemini_enterprise" {
  depends_on = [
    local_file.out_deregister_authorization_from_gemini_enterprise
  ]

  provisioner "local-exec" {
    when        = destroy
    command     = "./${path.module}/build/_deregister_authorization_from_gemini_enterprise_tpl.sh"
    interpreter = ["/bin/bash", "-c"]
  }
}

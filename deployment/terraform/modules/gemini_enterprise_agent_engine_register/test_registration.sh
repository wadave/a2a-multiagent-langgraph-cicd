#!/bin/bash
# Mock variables that Terraform usually passes
export gemini_enterprise_agent_name="Test Hosting Agent"
export agent_description="This is a test agent"
export gemini_enterprise_tool_description="Answer questions"
export gcp_project="496235138247"
export agent_engine_location="us-central1"
export agent_engine_resource_name="7864466924388745216"
export joined_authorization_names_string='"test_auth"'
export authorization_ids_set=("test_auth")

source templates/_register_or_update_agent_engine_to_gemini_enterprise_tpl.sh
echo "$REQUEST_BODY"

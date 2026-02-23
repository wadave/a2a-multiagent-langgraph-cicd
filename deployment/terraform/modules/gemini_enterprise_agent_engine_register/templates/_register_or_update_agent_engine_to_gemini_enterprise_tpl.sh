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

#!/usr/bin/env bash

gcp_project="${gcp_project}"
gcp_project_number="${gcp_project_number}"
agent_engine_location="${agent_engine_location}"
gemini_enterprise_location="${gemini_enterprise_location}"
agent_engine_id="${agent_engine_id}"

if [[ "$gemini_enterprise_location" == "global" ]]; then
  api_endpoint="discoveryengine.googleapis.com"
else
  api_endpoint="$${gemini_enterprise_location}-discoveryengine.googleapis.com"
fi
agent_display_name="${agent_display_name}"
gemini_enterprise_agent_name="${gemini_enterprise_agent_name}"
agent_description="${agent_description}"
gemini_enterprise_tool_description="${gemini_enterprise_tool_description}"
collection_id="${collection_id}"
gemini_enterprise_app_id="${gemini_enterprise_app_id}"
authorization_ids_set=(
%{ for key, value in authorization_ids ~}
 "${value}"
%{ endfor ~}
)

declare -A authorization_names

# Loop through the array of authorization IDs
for authorization_id in "$${authorization_ids_set[@]}"; do
  authorization_name="projects/$${gcp_project_number}/locations/$${gemini_enterprise_location}/authorizations/$${authorization_id}"
  authorization_names["$authorization_id"]="$authorization_name"
done

joined_authorization_names_string=$(printf ", \"%s\"" "$${authorization_names[@]}")
joined_authorization_names_string="$${joined_authorization_names_string:2}"

# Fetch Agent Engine Resource ID by Display Name
echo -n "Fetching Gemini Enterprise Assistants by Display Name \"$${gemini_enterprise_agent_name}\": "
all_assistants_output=$(curl -s -X GET \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/projects/$${gcp_project}/locations/$${gemini_enterprise_location}/collections/$${collection_id}/engines/$${gemini_enterprise_app_id}/assistants/default_assistant/agents")

all_engines_error=$(echo "$${all_assistants_output}" | jq '.error')
if [[ "$${all_engines_error}" == "null" ]]; then
  echo "Success"
else
  echo "all_engines_error: '$${all_engines_error}'"
  echo "Failure: '$${all_assistants_output}'"
  exit 1
fi

#echo "$${all_assistants_output}"

gemini_enterprise_assistant_resource_name=""
if [[ "$${all_assistants_output}" != "{}" ]]; then
  gemini_enterprise_assistant_resource_name=$(echo "$${all_assistants_output}" | jq ".agents[] | select(.displayName == \"$${gemini_enterprise_agent_name}\")" | jq '.name' | sed -e 's/"//'g)
fi

#echo "gemini_enterprise_assistant_resource_name: $${gemini_enterprise_assistant_resource_name}"

agent_engine_resource_name="$${agent_engine_id}"

if [ -z "$${agent_engine_resource_name}" ] || [ "$${agent_engine_resource_name}" == "unset" ]; then
  echo "No valid agent_engine_id provided. Cannot register resource with Gemini Enterprise."
  exit 1
fi

if [ $${#authorization_ids_set[@]} -eq 0 ]; then
  REQUEST_BODY=$(cat <<EOF
{
  "displayName": "$${gemini_enterprise_agent_name}",
  "description": "$${agent_description}",
  "a2aAgentDefinition": {
    "jsonAgentCard": "{ \"protocolVersion\": \"0.3.0\", \"name\": \"$${gemini_enterprise_agent_name}\", \"description\": \"$${agent_description}\", \"url\": \"https://$${agent_engine_location}-aiplatform.googleapis.com/v1beta1/$${agent_engine_resource_name}/a2a\", \"version\": \"1.0.0\", \"capabilities\": {}, \"skills\": [{ \"id\": \"question_answer\", \"name\": \"Q&A Agent\", \"description\": \"$${gemini_enterprise_tool_description}\", \"tags\": [\"Question-Answer\"] }], \"defaultInputModes\": [\"text\"], \"defaultOutputModes\": [\"text\"] }"
  }
}
EOF
)
else
  REQUEST_BODY=$(cat <<EOF
{
  "displayName": "$${gemini_enterprise_agent_name}",
  "description": "$${agent_description}",
  "a2aAgentDefinition": {
    "jsonAgentCard": "{ \"protocolVersion\": \"0.3.0\", \"name\": \"$${gemini_enterprise_agent_name}\", \"description\": \"$${agent_description}\", \"url\": \"https://$${agent_engine_location}-aiplatform.googleapis.com/v1beta1/$${agent_engine_resource_name}/a2a\", \"version\": \"1.0.0\", \"capabilities\": {}, \"skills\": [{ \"id\": \"question_answer\", \"name\": \"Q&A Agent\", \"description\": \"$${gemini_enterprise_tool_description}\", \"tags\": [\"Question-Answer\"] }], \"defaultInputModes\": [\"text\"], \"defaultOutputModes\": [\"text\"] }"
  },
  "authorization_config": {
    "agent_authorization": $${joined_authorization_names_string}
  }
}
EOF
)
fi

if [ -z "$${gemini_enterprise_assistant_resource_name}" ]; then
  # Register Agent Engine Resource with Gemini Enterprise
  echo -n "Registering Agent Engine Resource \"$${agent_engine_resource_name}\" with Gemini Enterprise app \"$${gemini_enterprise_app_id}\": "
  register_output=$(curl -s -X POST \
      -H "Authorization: Bearer $(gcloud auth print-access-token)" \
      -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
      -H "content-type: application/json" \
      "https://$${api_endpoint}/v1alpha/projects/$${gcp_project}/locations/$${gemini_enterprise_location}/collections/$${collection_id}/engines/$${gemini_enterprise_app_id}/assistants/default_assistant/agents" \
      -d "$${REQUEST_BODY}")

  register_error=$(echo "$${register_output}" | jq '.error')
  if [[ "$${register_error}" == "null" ]]; then
    echo "Success"
  else
    echo "Failure: '$${register_output}'"
    exit 1
  fi

  echo "$${register_output}"
  exit 0
fi

# Updating Agent Engine Resource with Gemini Enterprise
echo -n "Updating Agent Engine Resource \"$${agent_engine_resource_name}\" on Gemini Enterprise app \"$${gemini_enterprise_app_id}\": "
patch_output=$(curl -s -X PATCH \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/$${gemini_enterprise_assistant_resource_name}" \
    -d "$${REQUEST_BODY}")

patch_error=$(echo "$${patch_output}" | jq '.error')
if [[ "$${patch_error}" == "null" ]]; then
  echo "Success"
else
  echo "Failure: '$${patch_output}'"
  exit 1
fi

echo "$${patch_output}"
exit 0

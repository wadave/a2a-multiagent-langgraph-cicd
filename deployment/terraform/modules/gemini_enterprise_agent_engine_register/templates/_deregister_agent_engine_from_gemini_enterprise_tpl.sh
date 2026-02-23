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
agent_engine_location="${agent_engine_location}"
gemini_enterprise_location="${gemini_enterprise_location}"

if [[ "$gemini_enterprise_location" == "global" ]]; then
  api_endpoint="discoveryengine.googleapis.com"
else
  api_endpoint="$${gemini_enterprise_location}-discoveryengine.googleapis.com"
fi
agent_display_name="${agent_display_name}"
gemini_enterprise_agent_name="${gemini_enterprise_agent_name}"
agent_description="${agent_description}"
collection_id="${collection_id}"
gemini_enterprise_app_id="${gemini_enterprise_app_id}"

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
  echo "Failure: '$${all_assistants_output}'"
  exit 1
fi

#echo "$${all_assistants_output}"

gemini_enterprise_assistant_resource_name=""
if [[ "$${all_assistants_output}" != "{}" ]]; then
  gemini_enterprise_assistant_resource_name=$(echo "$${all_assistants_output}" | jq ".agents[] | select(.displayName == \"$${gemini_enterprise_agent_name}\")" | jq '.name' | sed -e 's/"//'g)
fi

if [ -z "$${gemini_enterprise_assistant_resource_name}" ]; then
  echo "Gemini Enterprise Assistant not found with name $${gemini_enterprise_agent_name}.  Resource not registered with Gemini Enterprise."
  exit 0
fi

# Delete Gemini Enterprise Assistant Registration by Resource Name
echo -n "Deleting Gemini Enterprise Assistant by Resource Name \"$${gemini_enterprise_assistant_resource_name}\": "
delete_assistant_output=$(curl -s -X DELETE \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/$${gemini_enterprise_assistant_resource_name}")

all_engines_error=$(echo "$${delete_assistant_output}" | jq '.error')
if [[ "$${all_engines_error}" == "null" ]]; then
  echo "Success"
else
  echo "Failure: '$${delete_assistant_output}'"
  exit 1
fi

echo "$${delete_assistant_output}"
exit 0

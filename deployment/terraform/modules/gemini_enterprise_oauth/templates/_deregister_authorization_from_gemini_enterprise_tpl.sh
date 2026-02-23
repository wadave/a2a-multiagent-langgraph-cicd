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
gemini_enterprise_location="${gemini_enterprise_location}"

if [[ "$gemini_enterprise_location" == "global" ]]; then
  api_endpoint="discoveryengine.googleapis.com"
else
  api_endpoint="$${gemini_enterprise_location}-discoveryengine.googleapis.com"
fi
authorization_id="${authorization_id}"
authorization_name="projects/$${gcp_project_number}/locations/$${gemini_enterprise_location}/authorizations/$${authorization_id}"

# Fetch Discovery Engine Authorization by Name
echo -n "Fetching Discovery Engine Authorization \"$${authorization_name}\": "
authorization_fetch_output=$(curl -s -X GET \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/$${authorization_name}")

fetch_error_status=$(echo "$authorization_fetch_output" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('status', 'OK'))")

if [[ "$fetch_error_status" == "NOT_FOUND" ]]; then
  echo "Gemini Enterprise Authorization not found with authorization_id $${authorization_id}. Resource not registered with Gemini Enterprise."
  exit 0
elif [[ "$fetch_error_status" == "OK" ]]; then
  echo "Found (will delete)"
else
  echo "Failure: '$authorization_fetch_output'"
  exit 1
fi

# Delete Authorization Resource from Discovery Engine
echo -n "Deleting Authorization \"$${authorization_name}\" from Discovery Engine: "
delete_output=$(curl -s -X DELETE \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/$${authorization_name}")

register_error=$(echo "$delete_output" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('error', 'null')) if isinstance(d, dict) else print('null')")
if [[ "$register_error" == "null" ]]; then
  echo "Success"
else
  echo "Failure: '$delete_output'"
  exit 1
fi

echo "$${delete_output}"
exit 0

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
authorization_uri_base="${authorization_uri_base}"
authorization_id="${authorization_id}"
authorization_name="projects/$${gcp_project_number}/locations/$${gemini_enterprise_location}/authorizations/$${authorization_id}"

additional_vars="${additional_vars}"
scopes=(
%{ for key, value in scopes ~}
 "${value}"
%{ endfor ~}
)
user_scopes=(
%{ for key, value in user_scopes ~}
 "${value}"
%{ endfor ~}
)
token_uri="${token_uri}"

# encode scopes
joined_scopes=$(printf "%s " "$${scopes[@]}")
joined_scopes="$${joined_scopes% }"
encoded_scopes=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote_plus(sys.argv[1]))" "$joined_scopes")

# encode user_scopes
encoded_user_scopes=""
if [ $${#user_scopes[@]} -ne 0 ]; then
  joined_user_scopes=$(printf "%s " "$${user_scopes[@]}")
  joined_user_scopes="$${joined_user_scopes% }"
  encoded_user_scopes=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote_plus(sys.argv[1]))" "$joined_user_scopes")
fi

# --- Do not modify ---

# Wait for OAuth to propagate
sleep 5

# Export credentials directly since they are passed as inputs
export OAUTH_CLIENT_ID="${oauth_client_id}"
export OAUTH_CLIENT_SECRET="${oauth_client_secret}"

authorization_uri="$${authorization_uri_base}?"
authorization_uri+="client_id=$${OAUTH_CLIENT_ID}"
authorization_uri+="&scope=$${encoded_scopes}"
if [ $${#user_scopes[@]} -ne 0 ]; then
  authorization_uri+="&user_scope=$${encoded_user_scopes}"
fi
authorization_uri+="$${additional_vars}"

# Fetch Discovery Engine Authorization by Name
echo -n "Fetching Discovery Engine Authorization \"$${authorization_name}\": "
authorization_fetch_output=$(curl -s -X GET \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/$${authorization_name}")

fetch_error_status=$(echo "$authorization_fetch_output" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('status', 'OK'))")

if [[ "$fetch_error_status" == "NOT_FOUND" ]]; then
  echo "Not Found (will create)"
  gemini_enterprise_authorization_resource_name=""
elif [[ "$fetch_error_status" == "OK" ]]; then
  echo "Found (will update)"
  gemini_enterprise_authorization_resource_name=$(echo "$authorization_fetch_output" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', ''))")
else
  echo "Failure: '$authorization_fetch_output'"
  exit 1
fi

# Create request payload
REQUEST_BODY=$(cat <<EOF
{
  "name": "$${authorization_name}",
  "serverSideOauth2": {
    "clientId": "$${OAUTH_CLIENT_ID}",
    "clientSecret": "$${OAUTH_CLIENT_SECRET}",
    "authorizationUri": "$${authorization_uri}",
    "tokenUri": "$${token_uri}"
  }
}
EOF
)


# Create if missing
if [ -z "$${gemini_enterprise_authorization_resource_name}" ]; then
  # Register Authorization Resource with Discovery Engine
  echo -n "Registering Authorization \"$${authorization_name}\" with Discovery Engine: "
  register_output=$(curl -s -X POST \
      -H "Authorization: Bearer $(gcloud auth print-access-token)" \
      -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
      -H "content-type: application/json" \
      "https://$${api_endpoint}/v1alpha/projects/$${gcp_project}/locations/$${gemini_enterprise_location}/authorizations?authorizationId=$${authorization_id}" \
      -d "$${REQUEST_BODY}")

  register_error=$(echo "$register_output" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'null'))")
  if [[ "$register_error" == "null" ]]; then
    echo "Success"
  else
    echo "Failure: '$register_output'"
    exit 1
  fi

  echo "$register_output"
  exit 0
fi

# Update Authorization Resource with Discovery Engine
echo -n "Updating Authorization \"$${authorization_name}\" on Discovery Engine: "
register_output=$(curl -s -X PATCH \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: $(gcloud config get-value project 2>&1 | grep -v 'active config')" \
    -H "content-type: application/json" \
    "https://$${api_endpoint}/v1alpha/projects/$${gcp_project}/locations/$${gemini_enterprise_location}/authorizations/$${authorization_id}" \
    -d "$${REQUEST_BODY}")

register_error=$(echo "$register_output" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'null'))")
if [[ "$register_error" == "null" ]]; then
  echo "Success"
else
  echo "Failure: '$register_output'"
  exit 1
fi

echo "$${register_output}"
exit 0

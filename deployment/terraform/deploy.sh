#!/bin/bash
# Local Terraform deployment helper.
# Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]
#
# All Terraform variable values are read from terraform.tfvars (auto-loaded by Terraform).
# Copy terraform.tfvars.example -> terraform.tfvars and fill in your values before running.
#
# This script additionally:
#   1. Reads cicd_runner_project_id from terraform.tfvars to locate the GCS state bucket.
#   2. Retrieves the latest agent engine ID from GCS state and passes it as the only
#      dynamic -var flag (since it changes on each agent deploy).
#   3. Ensures the GCS state bucket exists and initialises the Terraform backend.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENV="${1:-staging}"
ACTION="${2:-plan}"

if [[ "$ENV" != "staging" && "$ENV" != "prod" ]]; then
    echo -e "${RED}Error: Environment must be 'staging' or 'prod'${NC}"
    echo "Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]"
    exit 1
fi

if [[ "$ACTION" != "plan" && "$ACTION" != "apply" && "$ACTION" != "destroy" ]]; then
    echo -e "${RED}Error: Action must be 'plan', 'apply', or 'destroy'${NC}"
    echo "Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]"
    exit 1
fi

# Require terraform.tfvars — all variable values live there
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TFVARS="${SCRIPT_DIR}/terraform.tfvars"
if [[ ! -f "$TFVARS" ]]; then
    echo -e "${RED}Error: terraform.tfvars not found at ${TFVARS}${NC}"
    echo "Copy the example and fill in your values:"
    echo "  cp terraform.tfvars.example terraform.tfvars"
    exit 1
fi

# Parse PROJECT_ID and REGION from terraform.tfvars for GCS/state operations
_parse_tfvar() {
    grep -E "^${1}\s*=" "$TFVARS" | sed 's/.*=\s*"\?\([^"#]*\)"\?.*/\1/' | tr -d ' ' | head -1
}

PROJECT_ID="$(_parse_tfvar cicd_runner_project_id)"
REGION="$(_parse_tfvar region)"
REGION="${REGION:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
    echo -e "${RED}Error: cicd_runner_project_id not found in terraform.tfvars${NC}"
    exit 1
fi

BUCKET="${PROJECT_ID}-terraform-state"
PREFIX="a2a-multiagent-langgraph-cicd/${ENV}"

echo -e "${GREEN}==========================================="
echo "Terraform Deployment (local)"
echo -e "===========================================${NC}"
echo -e "Environment : ${YELLOW}${ENV}${NC}"
echo -e "Action      : ${YELLOW}${ACTION}${NC}"
echo -e "Project     : ${YELLOW}${PROJECT_ID}${NC}"
echo -e "State bucket: ${YELLOW}gs://${BUCKET}/${PREFIX}${NC}"
echo ""

# Step 1: Retrieve agent engine ID from GCS state
echo -e "${GREEN}Step 1: Retrieving agent state from GCS...${NC}"
AGENT_ENGINE_ID="unset"
STATE_URI="gs://${BUCKET}/${PREFIX}/agent_state.json"

if gcloud storage cat "${STATE_URI}" > /tmp/agent_state.json 2>/dev/null; then
    HOSTING_AGENT=$(jq -r '.agents.hosting.resource_name // empty' /tmp/agent_state.json)
    if [[ -n "$HOSTING_AGENT" ]]; then
        AGENT_ENGINE_ID="$HOSTING_AGENT"
        echo -e "${GREEN}✓ Retrieved agent ID from state${NC}"
    else
        echo -e "${YELLOW}⚠ No hosting agent found in state (first deploy?)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ State file not found — using 'unset'${NC}"
fi

# Step 2: Ensure GCS state bucket exists
echo -e "\n${GREEN}Step 2: Ensuring Terraform state bucket exists...${NC}"
if gcloud storage buckets describe "gs://${BUCKET}" 2>/dev/null > /dev/null; then
    echo -e "${GREEN}✓ Bucket exists: gs://${BUCKET}${NC}"
else
    echo -e "${YELLOW}Creating bucket: gs://${BUCKET}${NC}"
    gcloud storage buckets create "gs://${BUCKET}" \
        --location="${REGION}" \
        --project="${PROJECT_ID}"
    echo -e "${GREEN}✓ Bucket created${NC}"
fi

# Step 3: Initialise Terraform backend
echo -e "\n${GREEN}Step 3: Initialising Terraform backend...${NC}"
terraform init \
    -backend-config="bucket=${BUCKET}" \
    -backend-config="prefix=${PREFIX}" \
    -reconfigure
echo -e "${GREEN}✓ Terraform initialised${NC}"

# Step 4: Run Terraform
# terraform.tfvars is auto-loaded — only agent_engine_id is passed dynamically
# because it is resolved at runtime from GCS state above.
echo -e "\n${GREEN}Step 4: Running terraform ${ACTION}...${NC}"

case "$ACTION" in
    plan)
        terraform plan \
            -var="agent_engine_id=${AGENT_ENGINE_ID}"
        ;;
    apply)
        terraform apply -auto-approve \
            -var="agent_engine_id=${AGENT_ENGINE_ID}"
        echo -e "\n${GREEN}==========================================="
        echo "Deployment Complete!"
        echo -e "===========================================${NC}"
        terraform output
        ;;
    destroy)
        echo -e "${RED}⚠ WARNING: This will destroy all managed Cloud Run services!${NC}"
        read -r -p "Are you sure? (yes/no): " confirm
        if [[ "$confirm" == "yes" ]]; then
            terraform destroy -auto-approve \
                -var="agent_engine_id=${AGENT_ENGINE_ID}"
            echo -e "${GREEN}✓ Resources destroyed${NC}"
        else
            echo -e "${YELLOW}Destroy cancelled${NC}"
            exit 0
        fi
        ;;
esac

echo -e "${GREEN}✓ Done!${NC}"

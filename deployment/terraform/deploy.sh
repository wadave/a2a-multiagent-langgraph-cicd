#!/bin/bash
# Local Terraform deployment helper for infrastructure.
# Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]
#
# This manages INFRA only (SAs, IAM, APIs, Cloud Build triggers, Cloud Run shells).
# App deployments (agent code, images) are handled by Cloud Build pipelines.
#
# All Terraform variable values are read from terraform.tfvars (auto-loaded).
# Copy terraform.tfvars.example -> terraform.tfvars and fill in your values.

set -e

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

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TFVARS="${SCRIPT_DIR}/terraform.tfvars"
if [[ ! -f "$TFVARS" ]]; then
    echo -e "${RED}Error: terraform.tfvars not found at ${TFVARS}${NC}"
    echo "Copy the example and fill in your values:"
    echo "  cp terraform.tfvars.example terraform.tfvars"
    exit 1
fi

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
echo "Terraform Infrastructure Deployment (local)"
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
        echo -e "${GREEN}Retrieved agent ID from state${NC}"
    else
        echo -e "${YELLOW}No hosting agent found in state (first deploy?)${NC}"
    fi
else
    echo -e "${YELLOW}State file not found — using 'unset'${NC}"
fi

# Step 2: Ensure GCS state bucket exists
echo -e "\n${GREEN}Step 2: Ensuring Terraform state bucket exists...${NC}"
if gcloud storage buckets describe "gs://${BUCKET}" 2>/dev/null > /dev/null; then
    echo -e "${GREEN}Bucket exists: gs://${BUCKET}${NC}"
else
    echo -e "${YELLOW}Creating bucket: gs://${BUCKET}${NC}"
    gcloud storage buckets create "gs://${BUCKET}" \
        --location="${REGION}" \
        --project="${PROJECT_ID}"
    echo -e "${GREEN}Bucket created${NC}"
fi

# Step 3: Initialise Terraform backend
echo -e "\n${GREEN}Step 3: Initialising Terraform backend...${NC}"
terraform init \
    -backend-config="bucket=${BUCKET}" \
    -backend-config="prefix=${PREFIX}" \
    -reconfigure
echo -e "${GREEN}Terraform initialised${NC}"

# Step 4: Run Terraform
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
        echo "Infrastructure Deployment Complete!"
        echo -e "===========================================${NC}"
        terraform output
        ;;
    destroy)
        echo -e "${RED}WARNING: This will destroy all managed infrastructure!${NC}"
        read -r -p "Are you sure? (yes/no): " confirm
        if [[ "$confirm" == "yes" ]]; then
            terraform destroy -auto-approve \
                -var="agent_engine_id=${AGENT_ENGINE_ID}"
            echo -e "${GREEN}Resources destroyed${NC}"
        else
            echo -e "${YELLOW}Destroy cancelled${NC}"
            exit 0
        fi
        ;;
esac

echo -e "${GREEN}Done!${NC}"

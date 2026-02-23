#!/bin/bash
# Terraform Deployment Helper Script
# Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENV="${1:-staging}"
ACTION="${2:-plan}"

# Validate environment
if [[ "$ENV" != "staging" && "$ENV" != "prod" ]]; then
    echo -e "${RED}Error: Environment must be 'staging' or 'prod'${NC}"
    echo "Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]"
    exit 1
fi

# Validate action
if [[ "$ACTION" != "plan" && "$ACTION" != "apply" && "$ACTION" != "destroy" ]]; then
    echo -e "${RED}Error: Action must be 'plan', 'apply', or 'destroy'${NC}"
    echo "Usage: ./deploy.sh [staging|prod] [plan|apply|destroy]"
    exit 1
fi

# Set environment-specific variables
if [[ "$ENV" == "staging" ]]; then
    PROJECT_ID="dw-genai-dev"
    PROJECT_NUMBER="496235138247"
    REGION="us-central1"
    ENVIRONMENT="staging"
else
    PROJECT_ID="dw-genai-prod"
    PROJECT_NUMBER="101916374866"
    REGION="us-central1"
    ENVIRONMENT="prod"
fi

BUCKET="${PROJECT_ID}-terraform-state"
PREFIX="a2a-multiagent-langgraph-cicd/${ENVIRONMENT}"

echo -e "${GREEN}===========================================
Terraform Deployment Script
===========================================${NC}"
echo -e "Environment: ${YELLOW}$ENV${NC}"
echo -e "Action: ${YELLOW}$ACTION${NC}"
echo -e "Project: ${YELLOW}$PROJECT_ID${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"
echo ""

# Step 1: Retrieve agent state
echo -e "${GREEN}Step 1: Retrieving agent state...${NC}"
STATE_URI="gs://${BUCKET}/${PREFIX}/agent_state.json"
AGENT_ENGINE_ID="unset"

if gcloud storage cat "${STATE_URI}" > /tmp/agent_state.json 2>/dev/null; then
    HOSTING_AGENT=$(cat /tmp/agent_state.json | jq -r '.agents.hosting.resource_name // empty')
    if [ -n "$HOSTING_AGENT" ]; then
        AGENT_ENGINE_ID="$HOSTING_AGENT"
        echo -e "${GREEN}✓ Retrieved agent ID from state:${NC} ${AGENT_ENGINE_ID:0:80}..."
    else
        echo -e "${YELLOW}⚠ No hosting agent found in state file${NC}"
        echo -e "${YELLOW}⚠ Using default: unset${NC}"
    fi
else
    echo -e "${YELLOW}⚠ State file not found (first deployment)${NC}"
    echo -e "${YELLOW}⚠ Using default: unset${NC}"
fi

# Step 2: Ensure state bucket exists
echo -e "\n${GREEN}Step 2: Ensuring Terraform state bucket exists...${NC}"
if gcloud storage buckets describe gs://${BUCKET} 2>/dev/null > /dev/null; then
    echo -e "${GREEN}✓ Bucket exists:${NC} gs://${BUCKET}"
else
    echo -e "${YELLOW}Creating bucket:${NC} gs://${BUCKET}"
    gcloud storage buckets create gs://${BUCKET} \
        --location=${REGION} \
        --project=${PROJECT_ID}
    echo -e "${GREEN}✓ Bucket created${NC}"
fi

# Step 3: Initialize Terraform
echo -e "\n${GREEN}Step 3: Initializing Terraform...${NC}"
terraform init \
    -backend-config="bucket=${BUCKET}" \
    -backend-config="prefix=${PREFIX}" \
    -reconfigure

echo -e "${GREEN}✓ Terraform initialized${NC}"

# Step 4: Run Terraform action
echo -e "\n${GREEN}Step 4: Running Terraform ${ACTION}...${NC}"

COMMON_VARS=(
    -var="cicd_runner_project_id=${PROJECT_ID}"
    -var="staging_project_id=${PROJECT_ID}"
    -var="prod_project_id=${PROJECT_ID}"
    -var="project_number=${PROJECT_NUMBER}"
    -var="repository_name=a2a-multiagent-langgraph-cicd"
    -var="repository_owner=wadave"
    -var="agent_engine_id=${AGENT_ENGINE_ID}"
    -var="region=${REGION}"
)

if [ -f "test.tfvars" ]; then
    COMMON_VARS+=("-var-file=test.tfvars")
fi


case "$ACTION" in
    plan)
        terraform plan "${COMMON_VARS[@]}"
        ;;
    apply)
        terraform apply "${COMMON_VARS[@]}" -auto-approve

        # Get outputs
        echo -e "\n${GREEN}===========================================
Deployment Complete!
===========================================${NC}"
        echo -e "${GREEN}Outputs:${NC}"
        terraform output
        ;;
    destroy)
        echo -e "${RED}⚠ WARNING: This will destroy all Cloud Run services!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [[ "$confirm" == "yes" ]]; then
            terraform destroy "${COMMON_VARS[@]}" -auto-approve
            echo -e "${GREEN}✓ Resources destroyed${NC}"
        else
            echo -e "${YELLOW}Destroy cancelled${NC}"
            exit 0
        fi
        ;;
esac

echo -e "${GREEN}✓ Done!${NC}"

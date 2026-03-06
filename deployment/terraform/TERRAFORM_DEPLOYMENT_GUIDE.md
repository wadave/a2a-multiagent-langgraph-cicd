# Terraform Deployment Guide

## Quick Start from Scratch

### Prerequisites
1. Docker images must be built and pushed to GCR first
2. Agents must be deployed to get the `AGENT_ENGINE_ID`
3. GCS bucket for Terraform state will be auto-created

### Required Variables

All variables must be provided via `-var` flags or a `.tfvars` file:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `cicd_runner_project_id` | GCP project ID | `dw-genai-dev` | Yes |
| `staging_project_id` | Staging project ID | `dw-genai-dev` | Yes |
| `prod_project_id` | Production project ID | `dw-genai-prod` | Yes |
| `project_number` | GCP project number | `YOUR_PROJECT_NUMBER` | Yes |
| `repository_name` | GitHub repo name | `a2a-multiagent-langgraph-cicd` | Yes |
| `repository_owner` | GitHub owner | `wadave` | Yes |
| `agent_engine_id` | Full agent resource name | `projects/YOUR_PROJECT_NUMBER/locations/us-central1/reasoningEngines/...` | Yes (unless first deploy) |
| `region` | GCP region | `us-central1` | No (defaults to us-central1) |

### Environment Variables Set by Terraform

#### Frontend Service
- `PROJECT_ID` - From `var.cicd_runner_project_id`
- `PROJECT_NUMBER` - From `var.project_number`
- `GOOGLE_CLOUD_LOCATION` - From `var.region`
- `AGENT_ENGINE_ID` - From `var.agent_engine_id`

#### MCP Servers (Cocktail & Weather)
- No environment variables required (stateless services)

---

## Deployment Commands

### Option 1: Manual Deployment (Local)

```bash
# Navigate to Terraform directory
cd deployment/terraform

# Initialize Terraform with backend
terraform init \
  -backend-config="bucket=<PROJECT_ID>-terraform-state" \
  -backend-config="prefix=a2a-multiagent-langgraph-cicd/<ENV>"

# For staging
terraform init \
  -backend-config="bucket=dw-genai-dev-terraform-state" \
  -backend-config="prefix=a2a-multiagent-langgraph-cicd/staging"

# Plan deployment
terraform plan \
  -var="cicd_runner_project_id=dw-genai-dev" \
  -var="staging_project_id=dw-genai-dev" \
  -var="prod_project_id=dw-genai-dev" \
  -var="project_number=YOUR_PROJECT_NUMBER" \
  -var="repository_name=a2a-multiagent-langgraph-cicd" \
  -var="repository_owner=YOUR_GITHUB_USER" \
  -var="agent_engine_id=projects/YOUR_PROJECT_NUMBER/locations/us-central1/reasoningEngines/YOUR_REASONING_ENGINE_ID"  # pragma: allowlist secret

# Apply deployment
terraform apply \
  -var="cicd_runner_project_id=dw-genai-dev" \
  -var="staging_project_id=dw-genai-dev" \
  -var="prod_project_id=dw-genai-dev" \
  -var="project_number=YOUR_PROJECT_NUMBER" \
  -var="repository_name=a2a-multiagent-langgraph-cicd" \
  -var="repository_owner=YOUR_GITHUB_USER" \
  -var="agent_engine_id=projects/YOUR_PROJECT_NUMBER/locations/us-central1/reasoningEngines/YOUR_REASONING_ENGINE_ID"  # pragma: allowlist secret \
  -auto-approve
```

### Option 2: Using Variables File

Create `terraform.tfvars`:
```hcl
cicd_runner_project_id = "dw-genai-dev"
staging_project_id     = "dw-genai-dev"
prod_project_id        = "dw-genai-prod"
project_number         = "YOUR_PROJECT_NUMBER"
repository_name        = "a2a-multiagent-langgraph-cicd"
repository_owner       = "YOUR_GITHUB_USER"
agent_engine_id        = "projects/YOUR_PROJECT_NUMBER/locations/us-central1/reasoningEngines/YOUR_REASONING_ENGINE_ID"  # pragma: allowlist secret
region                 = "us-central1"
```

Then deploy:
```bash
terraform init \
  -backend-config="bucket=dw-genai-dev-terraform-state" \
  -backend-config="prefix=a2a-multiagent-langgraph-cicd/staging"

terraform plan
terraform apply -auto-approve
```

### Option 3: Deploy Single Service

Deploy only frontend:
```bash
terraform apply -target=google_cloud_run_v2_service.a2a_frontend \
  -var="..." \
  -auto-approve

# Force Cloud Run to pull new :latest image
gcloud run services update a2a-frontend-lg \
  --region=us-central1 \
  --project=dw-genai-dev \
  --image=gcr.io/dw-genai-dev/a2a-frontend-lg:latest
```

Deploy only Cocktail MCP server:
```bash
terraform apply -target=google_cloud_run_v2_service.cocktail_mcp_server \
  -var="..." \
  -auto-approve
```

Deploy only Weather MCP server:
```bash
terraform apply -target=google_cloud_run_v2_service.weather_mcp_server \
  -var="..." \
  -auto-approve
```

---

## Full Deployment from Scratch

### Step 1: Build Docker Images

```bash
# From project root
gcloud builds submit ./src/mcp_servers/cocktail_mcp_server \
  --tag gcr.io/dw-genai-dev/cocktail-remote-mcp-server-lg \
  --project dw-genai-dev

gcloud builds submit ./src/mcp_servers/weather_mcp_server \
  --tag gcr.io/dw-genai-dev/weather-remote-mcp-server-lg \
  --project dw-genai-dev

gcloud builds submit ./src/frontend \
  --tag gcr.io/dw-genai-dev/a2a-frontend-lg \
  --project dw-genai-dev
```

### Step 2: Deploy Agents

```bash
export PROJECT_ID=dw-genai-dev
export PROJECT_NUMBER=YOUR_PROJECT_NUMBER
export GOOGLE_CLOUD_REGION=us-central1
export ENVIRONMENT=staging
export CT_MCP_SERVER_URL='https://cocktail-remote-mcp-server-lg-YOUR_PROJECT_NUMBER.us-central1.run.app/mcp/'
export WEA_MCP_SERVER_URL='https://weather-remote-mcp-server-lg-YOUR_PROJECT_NUMBER.us-central1.run.app/mcp/'
export PYTHONPATH=src

python deployment/deploy_agents.py

# Capture the AGENT_ENGINE_ID from output
# Example: projects/YOUR_PROJECT_NUMBER/locations/us-central1/reasoningEngines/YOUR_REASONING_ENGINE_ID
```

### Step 3: Create Terraform State Bucket (if needed)

```bash
gcloud storage buckets create gs://dw-genai-dev-terraform-state \
  --location=us-central1 \
  --project=dw-genai-dev
```

### Step 4: Deploy Infrastructure via Terraform

```bash
cd deployment/terraform

terraform init \
  -backend-config="bucket=dw-genai-dev-terraform-state" \
  -backend-config="prefix=a2a-multiagent-langgraph-cicd/staging"

terraform apply \
  -var="cicd_runner_project_id=dw-genai-dev" \
  -var="staging_project_id=dw-genai-dev" \
  -var="prod_project_id=dw-genai-dev" \
  -var="project_number=YOUR_PROJECT_NUMBER" \
  -var="repository_name=a2a-multiagent-langgraph-cicd" \
  -var="repository_owner=YOUR_GITHUB_USER" \
  -var="agent_engine_id=<AGENT_ENGINE_ID_FROM_STEP_2>" \
  -auto-approve
```

### Step 5: Verify Deployment

```bash
# Check Cloud Run services
gcloud run services list --region=us-central1 --project=dw-genai-dev

# Get frontend URL
terraform output frontend_url

# Get all outputs
terraform output
```

---

## Troubleshooting

### Error: agent_engine_id validation failed
**Cause:** Invalid or missing agent engine ID

**Solution:**
1. Check the agent ID format: `projects/{number}/locations/{region}/reasoningEngines/{id}`
2. For first deployment, use default: `agent_engine_id="unset"`
3. Deploy agents first to get the real ID

### Error: Cloud Run not pulling new :latest image
**Cause:** Cloud Run caches `:latest` tag

**Solution:**
```bash
gcloud run services update <SERVICE_NAME> \
  --region=us-central1 \
  --project=dw-genai-dev \
  --image=gcr.io/dw-genai-dev/<IMAGE_NAME>:latest
```

### Error: Terraform state locked
**Cause:** Another Terraform operation is running

**Solution:**
```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Error: Backend bucket doesn't exist
**Cause:** GCS bucket not created

**Solution:**
```bash
gcloud storage buckets create gs://<PROJECT_ID>-terraform-state \
  --location=<REGION> \
  --project=<PROJECT_ID>
```

---

## CI/CD Pipeline Variables

The CI/CD pipeline (`.github/workflows/deploy.yml`) automatically passes all required variables:

**Staging:**
- `PROJECT_ID`: `dw-genai-dev`
- `PROJECT_NUMBER`: `YOUR_PROJECT_NUMBER`
- `REGION`: `us-central1`

**Production:**
- `PROJECT_ID`: `dw-genai-prod`
- `PROJECT_NUMBER`: `101916374866`
- `REGION`: `us-central1`

**Dynamic Variables:**
- `agent_engine_id`: Retrieved from persisted state or freshly deployed agents
- Repository info: Hardcoded in workflow

---

## Resource Naming Convention

All resources use consistent naming:

| Resource | Name | Pattern |
|----------|------|---------|
| Cocktail MCP Server | `cocktail-remote-mcp-server-lg` | `{service}-remote-mcp-server-lg` |
| Weather MCP Server | `weather-remote-mcp-server-lg` | `{service}-remote-mcp-server-lg` |
| Frontend | `a2a-frontend-lg` | `a2a-frontend-lg` |
| State Bucket | `dw-genai-dev-terraform-state` | `{project_id}-terraform-state` |

---

## Security Notes

1. **IAM:** All Cloud Run services have public access (`allUsers` can invoke)
2. **Authentication:** MCP servers and frontend handle auth via Google Cloud IAM
3. **State Backend:** GCS bucket should have versioning enabled for rollback
4. **Secrets:** No secrets in Terraform - all passed via environment variables

---

## Clean Up

To destroy all resources:

```bash
terraform destroy \
  -var="cicd_runner_project_id=dw-genai-dev" \
  -var="staging_project_id=dw-genai-dev" \
  -var="prod_project_id=dw-genai-dev" \
  -var="project_number=YOUR_PROJECT_NUMBER" \
  -var="repository_name=a2a-multiagent-langgraph-cicd" \
  -var="repository_owner=YOUR_GITHUB_USER" \
  -var="agent_engine_id=unset" \
  -auto-approve
```

**Note:** This does NOT delete:
- Docker images in GCR
- Vertex AI agents
- GCS state bucket
- Agent state files

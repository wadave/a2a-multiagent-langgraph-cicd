# Clean Redeploy Guide

## Problem: Manual Resource Deletion + CI/CD

If you manually delete all deployed resources and run CI/CD, **it will NOT work** due to:

1. ❌ **Path filters**: CI/CD steps only run when specific files change
2. ❌ **Terraform state**: State file references non-existent resources
3. ❌ **No triggers**: Deleting resources doesn't trigger redeployment

---

## Solution: Clean Redeploy from Scratch

### Method 1: Manual Cleanup + Workflow Dispatch (Recommended)

#### Step 1: Clean Up Terraform State

```bash
# Option A: Delete the entire state bucket (nuclear option)
gcloud storage buckets delete gs://dw-genai-dev-terraform-state --project=dw-genai-dev

# Option B: Delete just the state file
gcloud storage rm gs://dw-genai-dev-terraform-state/a2a-multiagent-langgraph-cicd/staging/default.tfstate
```

#### Step 2: Delete Resources (if not already done)

```bash
# Delete Cloud Run services
gcloud run services delete a2a-frontend-lg --region=us-central1 --project=dw-genai-dev --quiet
gcloud run services delete cocktail-remote-mcp-server-lg --region=us-central1 --project=dw-genai-dev --quiet
gcloud run services delete weather-remote-mcp-server-lg --region=us-central1 --project=dw-genai-dev --quiet

# Delete Reasoning Engines (Agent Engine)
# Get list first
gcloud ai reasoning-engines list --region=us-central1 --project=dw-genai-dev

# Delete each one
gcloud ai reasoning-engines delete 4971924510593777664 --region=us-central1 --project=dw-genai-dev --quiet
gcloud ai reasoning-engines delete 2922892233256468480 --region=us-central1 --project=dw-genai-dev --quiet
gcloud ai reasoning-engines delete 3747050965065269248 --region=us-central1 --project=dw-genai-dev --quiet

# Delete Container Images (optional)
gcloud container images delete gcr.io/dw-genai-dev/a2a-frontend-lg:latest --quiet
gcloud container images delete gcr.io/dw-genai-dev/cocktail-remote-mcp-server-lg:latest --quiet
gcloud container images delete gcr.io/dw-genai-dev/weather-remote-mcp-server-lg:latest --quiet
```

#### Step 3: Trigger Full Redeploy

**Option A: Use Workflow Dispatch (GitHub UI)**
1. Go to GitHub Actions → "Deploy A2A Multiagent App" workflow
2. Click "Run workflow"
3. Check "Force deploy all components"
4. Click "Run workflow"

**Option B: Make a dummy commit to trigger all paths**
```bash
# Touch files to trigger all path filters
touch src/mcp_servers/cocktail_mcp_server/.trigger
touch src/mcp_servers/weather_mcp_server/.trigger
touch src/a2a_agents/common/.trigger
touch src/frontend/.trigger
touch deployment/terraform/.trigger

git add .
git commit -m "chore: trigger full redeploy"
git push origin staging
```

**Option C: Update workflow conditions**
See Method 2 below for automated solution.

---

### Method 2: Add Force Deploy Flag (Automated)

Update the workflow to bypass path filters when `force_deploy_all` is true:

#### Add this step after "Detect Changes" step:

```yaml
- name: Override changes for force deploy
  if: github.event.inputs.force_deploy_all == 'true'
  run: |
    echo "cocktail_mcp=true" >> $GITHUB_OUTPUT
    echo "weather_mcp=true" >> $GITHUB_OUTPUT
    echo "agents=true" >> $GITHUB_OUTPUT
    echo "frontend=true" >> $GITHUB_OUTPUT
    echo "terraform=true" >> $GITHUB_OUTPUT
```

Then update ALL conditional steps from:
```yaml
if: steps.changes.outputs.agents == 'true'
```

To:
```yaml
if: steps.changes.outputs.agents == 'true' || github.event.inputs.force_deploy_all == 'true'
```

---

### Method 3: Separate "Deploy from Scratch" Workflow

Create `.github/workflows/deploy-clean.yml`:

```yaml
name: Deploy from Scratch

on:
  workflow_dispatch:

env:
  REGION: us-central1
  SERVICE_NAME: a2a-frontend-lg
  PYTHON_VERSION: '3.12'

jobs:
  deploy-clean:
    runs-on: ubuntu-latest
    environment: staging
    permissions:
      contents: 'read'
      id-token: 'write'

    env:
      PROJECT_ID: dw-genai-dev
      PROJECT_NUMBER: '496235138247'
      WORKLOAD_IDENTITY_PROVIDER: 'projects/496235138247/locations/global/workloadIdentityPools/github/providers/github-actions'
      SERVICE_ACCOUNT: 'github-runner@dw-genai-dev.iam.gserviceaccount.com'

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: '${{ env.WORKLOAD_IDENTITY_PROVIDER }}'
          service_account: '${{ env.SERVICE_ACCOUNT }}'

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      # Clean up Terraform state
      - name: Clean Terraform State
        run: |
          gcloud storage rm gs://${{ env.PROJECT_ID }}-terraform-state/a2a-multiagent-langgraph-cicd/staging/default.tfstate || true

      # Deploy MCP Servers
      - name: Deploy Cocktail MCP Server
        run: |
          gcloud builds submit ./src/mcp_servers/cocktail_mcp_server \
            --tag gcr.io/${{ env.PROJECT_ID }}/cocktail-remote-mcp-server-lg \
            --project ${{ env.PROJECT_ID }}

      - name: Deploy Weather MCP Server
        run: |
          gcloud builds submit ./src/mcp_servers/weather_mcp_server \
            --tag gcr.io/${{ env.PROJECT_ID }}/weather-remote-mcp-server-lg \
            --project ${{ env.PROJECT_ID }}

      # Deploy Agents
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install keyrings.google-artifactregistry-auth
          .venv/bin/pip install -e . --extra-index-url https://us-python.pkg.dev/artifact-foundry-prod/ah-3p-staging-python/simple/

      - name: Run A2A Deploy Script
        id: deploy_agents
        env:
          PROJECT_ID: ${{ env.PROJECT_ID }}
          PROJECT_NUMBER: ${{ env.PROJECT_NUMBER }}
          GOOGLE_CLOUD_REGION: ${{ env.REGION }}
          CT_MCP_SERVER_URL: 'https://cocktail-remote-mcp-server-lg-${{ env.PROJECT_NUMBER }}.${{ env.REGION }}.run.app/mcp/'
          WEA_MCP_SERVER_URL: 'https://weather-remote-mcp-server-lg-${{ env.PROJECT_NUMBER }}.${{ env.REGION }}.run.app/mcp/'
          PYTHONPATH: src
        run: |
          .venv/bin/python deployment/deploy_agents.py

      # Deploy Frontend
      - name: Build Frontend Image
        run: |
          gcloud builds submit ./src/frontend \
            --tag gcr.io/${{ env.PROJECT_ID }}/a2a-frontend-lg \
            --project ${{ env.PROJECT_ID }}

      # Deploy Infrastructure
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Ensure Terraform state bucket exists
        run: |
          gcloud storage buckets describe gs://${{ env.PROJECT_ID }}-terraform-state 2>/dev/null || \
          gcloud storage buckets create gs://${{ env.PROJECT_ID }}-terraform-state \
            --location=${{ env.REGION }} --project=${{ env.PROJECT_ID }}

      - name: Terraform Init
        run: |
          terraform init \
            -backend-config="bucket=${{ env.PROJECT_ID }}-terraform-state" \
            -backend-config="prefix=a2a-multiagent-langgraph-cicd/staging"
        working-directory: deployment/terraform

      - name: Terraform Apply
        run: |
          terraform apply -auto-approve \
            -var="cicd_runner_project_id=${{ env.PROJECT_ID }}" \
            -var="staging_project_id=${{ env.PROJECT_ID }}" \
            -var="prod_project_id=${{ env.PROJECT_ID }}" \
            -var="project_number=${{ env.PROJECT_NUMBER }}" \
            -var="repository_name=a2a-multiagent-langgraph-cicd" \
            -var="repository_owner=wadave" \
            -var="agent_engine_id=${{ steps.deploy_agents.outputs.AGENT_ENGINE_ID }}"
        working-directory: deployment/terraform
```

---

## Current CI/CD Limitations

### Path Filters Prevent Full Redeploy

The current workflow has conditionals that prevent redeployment:

```yaml
# These steps only run if specific paths changed
if: steps.changes.outputs.cocktail_mcp == 'true'    # src/mcp_servers/cocktail_mcp_server/**
if: steps.changes.outputs.weather_mcp == 'true'     # src/mcp_servers/weather_mcp_server/**
if: steps.changes.outputs.agents == 'true'          # src/a2a_agents/**
if: steps.changes.outputs.frontend == 'true'        # src/frontend/**
if: steps.changes.outputs.terraform == 'true'       # deployment/terraform/**
```

**Why this exists:** Optimization - don't rebuild/redeploy unchanged components.

**Problem:** If resources are deleted manually, CI/CD won't recreate them unless files change.

---

## Recommended Approach

### For Testing Clean Deployment

Use **Method 3** - Create a separate `deploy-clean.yml` workflow that:
- ✅ Always runs all steps (no path filters)
- ✅ Cleans Terraform state automatically
- ✅ Can be triggered manually via GitHub UI
- ✅ Doesn't interfere with normal CI/CD

### For Production

Keep the current workflow as-is for incremental updates, and use the clean deployment workflow only when:
- Setting up a new environment
- Recovering from manual deletions
- Testing full deployment from scratch

---

## Verification After Clean Redeploy

```bash
# 1. Check Cloud Run services
gcloud run services list --region=us-central1 --project=dw-genai-dev

# 2. Check Agent Engine deployments
gcloud ai reasoning-engines list --region=us-central1 --project=dw-genai-dev

# 3. Check Terraform state
gcloud storage ls gs://dw-genai-dev-terraform-state/a2a-multiagent-langgraph-cicd/staging/

# 4. Test frontend
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://a2a-frontend-lg-XXXX.run.app

# 5. Get frontend URL
gcloud run services describe a2a-frontend-lg --region=us-central1 --project=dw-genai-dev --format="value(status.url)"
```

---

## Summary

**Question:** Will CI/CD work after manual resource deletion?

**Answer:** ❌ **NO**, not without one of these fixes:

1. ✅ **Clean Terraform state** + trigger workflow manually
2. ✅ **Add force_deploy_all flag** to workflow
3. ✅ **Create separate clean deployment workflow** (recommended)
4. ✅ **Touch files to trigger path filters** + commit/push

**Root Cause:** CI/CD uses path-based conditionals for efficiency, which prevents redeployment of unchanged code even when resources are deleted.

**Recommended Solution:** Create `deploy-clean.yml` workflow for manual clean deployments while keeping existing workflow for incremental updates.

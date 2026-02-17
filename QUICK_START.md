# Quick Start: Deploy from Scratch

## Answer: Will CI/CD work after deleting all resources?

❌ **NO** - The current `deploy.yml` uses **path filters** that only run when specific files change.

✅ **YES** - If you use the new `deploy-clean.yml` workflow created for this purpose.

---

## Quick Redeploy Steps

### Option 1: Use Clean Deploy Workflow (GitHub UI) ⭐ RECOMMENDED

1. **Go to GitHub Actions**
   - Repository → Actions tab
   - Select "Deploy from Scratch (Clean)" workflow

2. **Run Workflow**
   - Click "Run workflow" button
   - Branch: `staging`
   - Clean Terraform state: ✅ (checked)
   - Click "Run workflow"

3. **Wait for completion** (~10 minutes)
   - MCP servers build and deploy
   - Agents deploy
   - Frontend builds and deploys
   - Terraform creates Cloud Run services

4. **Get Frontend URL**
   - Check workflow output
   - Or run: `gcloud run services describe a2a-frontend-lg --region=us-central1 --format="value(status.url)"`

---

### Option 2: Manual Deployment

```bash
# 1. Clean up (if resources exist)
gcloud storage rm gs://dw-genai-dev-terraform-state/a2a-multiagent-langgraph-cicd/staging/default.tfstate

# 2. Set environment variables
export PROJECT_ID=dw-genai-dev
export PROJECT_NUMBER=496235138247
export GOOGLE_CLOUD_REGION=us-central1
export CT_MCP_SERVER_URL=https://cocktail-remote-mcp-server-lg-${PROJECT_NUMBER}.${GOOGLE_CLOUD_REGION}.run.app/mcp/
export WEA_MCP_SERVER_URL=https://weather-remote-mcp-server-lg-${PROJECT_NUMBER}.${GOOGLE_CLOUD_REGION}.run.app/mcp/

# 3. Deploy MCP servers
gcloud builds submit ./src/mcp_servers/cocktail_mcp_server --tag gcr.io/${PROJECT_ID}/cocktail-remote-mcp-server-lg
gcloud builds submit ./src/mcp_servers/weather_mcp_server --tag gcr.io/${PROJECT_ID}/weather-remote-mcp-server-lg

# 4. Deploy agents
python deployment/deploy_agents.py
# Copy the AGENT_ENGINE_ID output

# 5. Deploy frontend
gcloud builds submit ./src/frontend --tag gcr.io/${PROJECT_ID}/a2a-frontend-lg

# 6. Deploy with Terraform
cd deployment/terraform
terraform init -backend-config="bucket=${PROJECT_ID}-terraform-state" -backend-config="prefix=a2a-multiagent-langgraph-cicd/dev"
terraform apply \
  -var="cicd_runner_project_id=${PROJECT_ID}" \
  -var="staging_project_id=${PROJECT_ID}" \
  -var="prod_project_id=${PROJECT_ID}" \
  -var="project_number=${PROJECT_NUMBER}" \
  -var="repository_name=a2a-multiagent-langgraph-cicd" \
  -var="repository_owner=wadave" \
  -var="agent_engine_id=<PASTE_AGENT_ENGINE_ID_HERE>"
```

---

## Why Current CI/CD Won't Work

The `deploy.yml` workflow uses **conditional deployment**:

```yaml
if: steps.changes.outputs.agents == 'true'    # Only if src/a2a_agents/** changed
if: steps.changes.outputs.frontend == 'true'  # Only if src/frontend/** changed
```

**Benefits:** Faster deployments, only rebuild what changed
**Drawback:** Won't redeploy if resources deleted but code unchanged

---

## Files Created

1. **`.github/workflows/deploy-clean.yml`** ⭐
   - Clean deployment workflow (no path filters)
   - Can be triggered manually from GitHub UI
   - Automatically cleans Terraform state
   - Deploys ALL components

2. **`CLEAN_REDEPLOY.md`**
   - Detailed guide on clean redeployment
   - Multiple methods and options
   - Troubleshooting steps

3. **`DEPLOYMENT_SUMMARY.md`**
   - Complete configuration overview
   - Environment variable flow
   - All changes made

---

## Workflow Comparison

| Feature | deploy.yml | deploy-clean.yml |
|---------|-----------|------------------|
| Trigger | Push to branch | Manual (workflow_dispatch) |
| Path filters | ✅ Yes (efficient) | ❌ No (always deploys all) |
| Terraform state cleanup | ❌ No | ✅ Yes (optional) |
| Use case | Incremental updates | Clean deployment |
| Speed | Fast (only changed) | Slower (all components) |

---

## Verification Commands

```bash
# Check Cloud Run services
gcloud run services list --region=us-central1

# Check Agent Engines
gcloud ai reasoning-engines list --region=us-central1

# Get frontend URL
gcloud run services describe a2a-frontend-lg --region=us-central1 --format="value(status.url)"

# Test frontend
curl -s -o /dev/null -w "HTTP %{http_code}\n" $(gcloud run services describe a2a-frontend-lg --region=us-central1 --format="value(status.url)")
```

---

## Troubleshooting

### Terraform State Conflicts
```bash
# Clean state and retry
gcloud storage rm gs://dw-genai-dev-terraform-state/a2a-multiagent-langgraph-cicd/staging/default.tfstate
```

### Agent Deployment Fails
```bash
# Check MCP servers are running
gcloud run services list --region=us-central1 | grep mcp-server

# Verify MCP server URLs
curl https://cocktail-remote-mcp-server-lg-496235138247.us-central1.run.app/mcp/
```

### Frontend 403 Error
```bash
# Add public IAM policy
gcloud run services add-iam-policy-binding a2a-frontend-lg \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

---

## Next Steps

1. ✅ Use **deploy-clean.yml** for initial deployment or after manual deletions
2. ✅ Use **deploy.yml** (existing) for regular code updates
3. ✅ Monitor deployments in GitHub Actions tab
4. ✅ Test frontend URL after deployment

**Frontend should be at:** https://a2a-frontend-lg-XXXXX.run.app

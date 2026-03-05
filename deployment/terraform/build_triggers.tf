# Fetch project numbers automatically from project IDs
data "google_project" "staging" {
  project_id = var.staging_project_id
}

data "google_project" "prod" {
  count      = var.prod_project_id != "" ? 1 : 0
  project_id = var.prod_project_id
}

# a. Create PR checks trigger
resource "google_cloudbuild_trigger" "pr_checks" {
  name            = "pr-${local.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for PR checks"
  service_account = google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
    pull_request {
      branch = "main"
    }
  }

  filename = ".cloudbuild/pr_checks.yaml"
  included_files = [
    "src/mcp_servers/**",
    "src/a2a_agents/**",
    "src/frontend/**",
    "tests/**",
    ".cloudbuild/**",
    "deployment/**",
    "uv.lock",
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  depends_on = [
    google_project_service.cicd_services,
    google_project_service.deploy_project_services,
  ]
}

# b. Create staging CD pipeline trigger
resource "google_cloudbuild_trigger" "cd_pipeline" {
  name            = "cd-${local.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  service_account = google_service_account.cicd_runner_sa.id
  description     = "Trigger for CD pipeline"

  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
    push {
      branch = "staging"
    }
  }

  filename = ".cloudbuild/staging.yaml"
  included_files = [
    "src/mcp_servers/**",
    "src/a2a_agents/**",
    "src/frontend/**",
    "tests/**",
    ".cloudbuild/**",
    "deployment/**",
    "uv.lock",
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _STAGING_PROJECT_ID          = var.staging_project_id
    _PROJECT_NUMBER              = data.google_project.staging.number
    _LOGS_BUCKET_NAME_STAGING    = google_storage_bucket.logs_data_bucket[var.staging_project_id].name
    _APP_SERVICE_ACCOUNT_STAGING = google_service_account.app_sa["staging"].email
    _REGION                      = var.region
    _GE_APP_STAGING              = var.ge_app_staging
  }
  depends_on = [
    google_project_service.cicd_services,
    google_project_service.deploy_project_services,
  ]
}

# c. Create deploy to production trigger
resource "google_cloudbuild_trigger" "deploy_to_prod_pipeline" {
  count           = var.prod_project_id != "" ? 1 : 0
  name            = "deploy-${local.project_name}"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for deployment to production"
  service_account = google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = "projects/${var.cicd_runner_project_id}/locations/${var.region}/connections/${var.host_connection_name}/repositories/${var.repository_name}"
  }

  filename           = ".cloudbuild/deploy-to-prod.yaml"
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  approval_config {
    approval_required = true
  }
  substitutions = {
    _PROD_PROJECT_ID          = var.prod_project_id
    _PROJECT_NUMBER           = var.prod_project_id != "" ? data.google_project.prod[0].number : ""
    _LOGS_BUCKET_NAME_PROD    = try(google_storage_bucket.logs_data_bucket[var.prod_project_id].name, "")
    _APP_SERVICE_ACCOUNT_PROD = try(google_service_account.app_sa["prod"].email, "")
    _REGION                   = var.region
    _GE_APP                   = var.ge_app_prod
    _AUTH_ID                  = var.auth_id
  }
  depends_on = [
    google_project_service.cicd_services,
    google_project_service.deploy_project_services,
  ]
}

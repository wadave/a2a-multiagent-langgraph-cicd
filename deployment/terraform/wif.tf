resource "google_iam_workload_identity_pool" "github" {
  project                   = "dw-genai-prod"
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "Identity pool for GitHub Actions"
  # Ignore already exists errors
  lifecycle {
    prevent_destroy = false
  }
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = "dw-genai-prod"
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions"
  display_name                       = "GitHub Actions Provider"
  description                        = "OIDC identity pool provider for execute GitHub Actions"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  attribute_condition = "assertion.repository == \"wadave/a2a-multiagent-langgraph-cicd\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_runner" {
  project      = "dw-genai-prod"
  account_id   = "github-runner"
  display_name = "GitHub Actions Runner"
  description  = "Service account for GitHub Actions runner"
}

resource "google_project_iam_member" "github_runner_editor" {
  project = "dw-genai-prod"
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_runner.email}"
}

resource "google_service_account_iam_member" "workload_identity_user" {
  service_account_id = google_service_account.github_runner.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/wadave/a2a-multiagent-langgraph-cicd"
}

output "workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "service_account" {
  value = google_service_account.github_runner.email
}

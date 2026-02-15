resource "google_iam_workload_identity_pool" "github" {
  project                   = var.cicd_runner_project_id
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "Identity pool for GitHub Actions"
  lifecycle {
    prevent_destroy = false
  }
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.cicd_runner_project_id
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

  attribute_condition = "assertion.repository == \"${var.repository_owner}/${var.repository_name}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_runner" {
  project      = var.cicd_runner_project_id
  account_id   = "github-runner"
  display_name = "GitHub Actions Runner"
  description  = "Service account for GitHub Actions runner"
}

resource "google_project_iam_member" "github_runner_editor" {
  project = var.cicd_runner_project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_runner.email}"
}

resource "google_project_iam_member" "compute_sa_storage_admin" {
  project = "dw-genai-prod"
  role    = "roles/storage.admin"
  member  = "serviceAccount:101916374866-compute@developer.gserviceaccount.com"
}

resource "google_service_account_iam_member" "workload_identity_user" {
  service_account_id = google_service_account.github_runner.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.repository_owner}/${var.repository_name}"
}

output "workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "service_account" {
  value = google_service_account.github_runner.email
}

# Data source to get project numbers
data "google_project" "projects" {
  for_each   = local.deploy_project_ids
  project_id = each.value
}

# 1. Assign roles for the CICD project
resource "google_project_iam_member" "cicd_project_roles" {
  for_each = toset(var.cicd_roles)

  project = var.cicd_runner_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}

# 2. Assign roles for staging/prod projects
resource "google_project_iam_member" "other_projects_roles" {
  for_each = {
    for pair in setproduct(toset(values(local.deploy_project_ids)), var.cicd_sa_deployment_required_roles) :
    "${pair[0]}-${pair[1]}" => {
      project_id = pair[0]
      role       = pair[1]
    }
  }

  project = each.value.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}

# 3. Grant application SA the required permissions
resource "google_project_iam_member" "app_sa_roles" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), var.app_sa_roles) :
    join(",", pair) => {
      project = local.deploy_project_ids[pair[0]]
      role    = pair[1]
    }
  }

  project = each.value.project
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.app_sa[split(",", each.key)[0]].email}"
}

# Allow the CICD SA to create tokens
resource "google_service_account_iam_member" "cicd_run_invoker_token_creator" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}

# Allow the CICD SA to impersonate itself
resource "google_service_account_iam_member" "cicd_run_invoker_account_user" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}

# Allow CICD SA to impersonate app service accounts for deployment
resource "google_service_account_iam_member" "cicd_impersonate_app_sa" {
  for_each = local.deploy_project_ids

  service_account_id = google_service_account.app_sa[each.key].name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}

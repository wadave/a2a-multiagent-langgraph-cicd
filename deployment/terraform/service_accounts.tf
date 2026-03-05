resource "google_service_account" "cicd_runner_sa" {
  account_id   = "${local.project_name}-cb"
  display_name = "CICD Runner SA"
  project      = var.cicd_runner_project_id
  depends_on   = [google_project_service.cicd_services, google_project_service.deploy_project_services]
}

resource "google_service_account" "app_sa" {
  for_each = local.deploy_project_ids

  account_id   = "${local.project_name}-app"
  display_name = "${local.project_name} Agent Service Account"
  project      = each.value
  depends_on   = [google_project_service.cicd_services, google_project_service.deploy_project_services]
}

resource "google_storage_bucket" "logs_data_bucket" {
  for_each                    = toset(local.all_project_ids)
  name                        = "${each.value}-${local.project_name}-logs"
  location                    = var.region
  project                     = each.value
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [google_project_service.cicd_services, google_project_service.deploy_project_services]
}

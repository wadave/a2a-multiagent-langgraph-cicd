# Use for_each (not count) so all APIs enable in parallel
resource "google_project_service" "cicd_services" {
  for_each = toset(local.cicd_services)

  project            = var.cicd_runner_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service" "deploy_project_services" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), local.deploy_project_services) :
    "${pair[0]}_${replace(pair[1], ".", "_")}" => {
      project = local.deploy_project_ids[pair[0]]
      service = pair[1]
    }
  }
  project            = each.value.project
  service            = each.value.service
  disable_on_destroy = false
}

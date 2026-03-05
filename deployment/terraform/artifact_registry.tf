# Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  project       = var.cicd_runner_project_id
  location      = var.region
  repository_id = local.project_name
  format        = "DOCKER"
  description   = "Docker images for ${local.project_name}"

  depends_on = [google_project_service.cicd_services]
}

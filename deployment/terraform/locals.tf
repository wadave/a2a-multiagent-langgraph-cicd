locals {
  project_name = "a2a-multiagent-lg-cicd"

  cicd_services = [
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "aiplatform.googleapis.com",
    "serviceusage.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
  ]

  deploy_project_services = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "discoveryengine.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "secretmanager.googleapis.com",
  ]

  deploy_project_ids = {
    for k, v in {
      staging = var.staging_project_id
      prod    = var.prod_project_id
    } : k => v if v != ""
  }

  all_project_ids = compact([
    var.cicd_runner_project_id,
    var.staging_project_id,
    var.prod_project_id
  ])
}

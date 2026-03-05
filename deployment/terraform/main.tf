terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project               = var.cicd_runner_project_id
  region                = var.region
  user_project_override = true
}

# Hybrid Provisioning: Terraform creates Cloud Run shells with a placeholder
# image. CI/CD then deploys the real image via `gcloud run deploy`, which
# updates the service in-place without Terraform interfering.

# Cloud Run Service for Cocktail MCP Server
resource "google_cloud_run_v2_service" "cocktail_mcp_server" {
  for_each            = local.deploy_project_ids
  deletion_protection = false
  name                = "cocktail-mcp-lg-${each.key}"
  location            = var.region
  project             = each.value

  template {
    timeout         = "300s"
    service_account = google_service_account.app_sa[each.key].email
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
      client,
      client_version,
    ]
  }
}

# Cloud Run Service for Weather MCP Server
resource "google_cloud_run_v2_service" "weather_mcp_server" {
  for_each            = local.deploy_project_ids
  deletion_protection = false
  name                = "weather-mcp-lg-${each.key}"
  location            = var.region
  project             = each.value

  template {
    timeout         = "300s"
    service_account = google_service_account.app_sa[each.key].email
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
      client,
      client_version,
    ]
  }
}

# Cloud Run Service for the A2A Frontend
resource "google_cloud_run_v2_service" "a2a_frontend" {
  for_each            = local.deploy_project_ids
  deletion_protection = false
  name                = "a2a-frontend-lg-${each.key}"
  location            = var.region
  project             = each.value

  template {
    timeout         = "300s"
    service_account = google_service_account.app_sa[each.key].email
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
      client,
      client_version,
    ]
  }
}

# IAM policy to allow public access to frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public_access" {
  for_each = local.deploy_project_ids

  name     = google_cloud_run_v2_service.a2a_frontend[each.key].name
  location = google_cloud_run_v2_service.a2a_frontend[each.key].location
  project  = google_cloud_run_v2_service.a2a_frontend[each.key].project
  role     = "roles/run.invoker"
  member   = "allUsers"
}

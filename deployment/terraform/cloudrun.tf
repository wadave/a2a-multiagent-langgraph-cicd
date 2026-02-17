# Cloud Run Service for Cocktail MCP Server
resource "google_cloud_run_v2_service" "cocktail_mcp_server" {
  deletion_protection = false
  name     = "cocktail-remote-mcp-server-lg"
  location = var.region
  project  = var.cicd_runner_project_id

  template {
    timeout = "300s"
    containers {
      image = "gcr.io/${var.cicd_runner_project_id}/cocktail-remote-mcp-server-lg:latest"
      
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
}

# Cloud Run Service for Weather MCP Server
resource "google_cloud_run_v2_service" "weather_mcp_server" {
  deletion_protection = false
  name     = "weather-remote-mcp-server-lg"
  location = var.region
  project  = var.cicd_runner_project_id

  template {
    timeout = "300s"
    containers {
      image = "gcr.io/${var.cicd_runner_project_id}/weather-remote-mcp-server-lg:latest"
      
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
}

# Cloud Run Service for the A2A Frontend
resource "google_cloud_run_v2_service" "a2a_frontend" {
  deletion_protection = false
  name     = "a2a-frontend-lg"
  location = var.region
  project  = var.cicd_runner_project_id

  template {
    timeout = "300s"
    containers {
      image = "gcr.io/${var.cicd_runner_project_id}/a2a-frontend-lg:latest"
      
      env {
        name  = "PROJECT_ID"
        value = var.cicd_runner_project_id
      }

      env {
        name  = "PROJECT_NUMBER"
        value = var.project_number
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name  = "AGENT_ENGINE_ID"
        # This will be injected dynamically if deploying agents outside Terraform,
        # or replaced by a known value if deployed within Terraform
        value = var.agent_engine_id
      }

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
}

# IAM policy to allow public access to frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public_access" {
  name     = google_cloud_run_v2_service.a2a_frontend.name
  location = google_cloud_run_v2_service.a2a_frontend.location
  project  = google_cloud_run_v2_service.a2a_frontend.project
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM policy to allow public access to cocktail MCP server
resource "google_cloud_run_v2_service_iam_member" "cocktail_mcp_public_access" {
  name     = google_cloud_run_v2_service.cocktail_mcp_server.name
  location = google_cloud_run_v2_service.cocktail_mcp_server.location
  project  = google_cloud_run_v2_service.cocktail_mcp_server.project
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM policy to allow public access to weather MCP server
resource "google_cloud_run_v2_service_iam_member" "weather_mcp_public_access" {
  name     = google_cloud_run_v2_service.weather_mcp_server.name
  location = google_cloud_run_v2_service.weather_mcp_server.location
  project  = google_cloud_run_v2_service.weather_mcp_server.project
  role     = "roles/run.invoker"
  member   = "allUsers"
}


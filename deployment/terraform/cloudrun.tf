# Cloud Run Service for Cocktail MCP Server
resource "google_cloud_run_v2_service" "cocktail_mcp_server" {
  name     = "cocktail-remote-mcp-server-lg"
  location = var.region
  project  = var.cicd_runner_project_id

  template {
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
  name     = "weather-remote-mcp-server-lg"
  location = var.region
  project  = var.cicd_runner_project_id

  template {
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
  name     = "a2a-frontend-lg"
  location = var.region
  project  = var.cicd_runner_project_id

  template {
    containers {
      image = "gcr.io/${var.cicd_runner_project_id}/a2a-frontend-lg:latest"
      
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

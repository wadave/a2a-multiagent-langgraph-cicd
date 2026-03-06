# Hybrid Provisioning: Terraform creates Agent Engine shells with a dummy source.
# CI/CD then updates with actual agent code via the Python SDK (deploy_agents.py).

locals {
  # Read base64-encoded dummy source tarball from local file
  dummy_source_b64 = trimspace(file("${path.module}/dummy/source-b64.txt"))

  # Agent definitions - display_name must match what deploy_agents.py uses
  agents = {
    cocktail = {
      display_name = "Cocktail Agent LangGraph"
      description  = "A2A agent for cocktail information"
    }
    weather = {
      display_name = "Weather Agent LangGraph"
      description  = "A2A agent for weather forecasts"
    }
    hosting = {
      display_name = "Hosting Agent LangGraph"
      description  = "Orchestrator agent that delegates to specialist agents"
    }
  }
}

resource "google_vertex_ai_reasoning_engine" "agent" {
  for_each = {
    for combo in setproduct(keys(local.deploy_project_ids), keys(local.agents)) :
    "${combo[0]}-${combo[1]}" => {
      env          = combo[0]
      project      = local.deploy_project_ids[combo[0]]
      display_name = local.agents[combo[1]].display_name
      description  = local.agents[combo[1]].description
    }
  }

  display_name = each.value.display_name
  description  = each.value.description
  region       = var.region
  project      = each.value.project

  spec {
    service_account = google_service_account.app_sa[each.value.env].email

    deployment_spec {
      min_instances         = 1
      max_instances         = 10
      container_concurrency = 9

      resource_limits = {
        cpu    = "4"
        memory = "8Gi"
      }
    }

    source_code_spec {
      inline_source {
        source_archive = local.dummy_source_b64
      }

      python_spec {
        entrypoint_module = "app.agent_engine_app"
        entrypoint_object = "agent_engine"
        requirements_file = "app/app_utils/.requirements.txt"
        version           = "3.12"
      }
    }
  }

  lifecycle {
    ignore_changes = [
      spec[0].source_code_spec,
      spec[0].deployment_spec[0].env,
      spec[0].agent_framework,
    ]
  }

  depends_on = [google_project_service.deploy_project_services]
}

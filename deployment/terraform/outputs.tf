output "frontend_urls" {
  description = "URLs of the deployed frontend services"
  value       = { for k, v in google_cloud_run_v2_service.a2a_frontend : k => v.uri }
}

output "agent_engine_id_used" {
  description = "The agent engine ID configured in the frontend"
  value       = var.agent_engine_id
  sensitive   = false
}

output "cocktail_mcp_urls" {
  description = "URLs of the Cocktail MCP servers"
  value       = { for k, v in google_cloud_run_v2_service.cocktail_mcp_server : k => v.uri }
}

output "weather_mcp_urls" {
  description = "URLs of the Weather MCP servers"
  value       = { for k, v in google_cloud_run_v2_service.weather_mcp_server : k => v.uri }
}

output "cicd_runner_sa_email" {
  description = "Email of the CICD runner service account"
  value       = google_service_account.cicd_runner_sa.email
}

output "app_sa_emails" {
  description = "Emails of the application service accounts"
  value       = { for k, v in google_service_account.app_sa : k => v.email }
}

output "frontend_url" {
  description = "URL of the deployed frontend service"
  value       = google_cloud_run_v2_service.a2a_frontend.uri
}

output "agent_engine_id_used" {
  description = "The agent engine ID configured in the frontend"
  value       = var.agent_engine_id
  sensitive   = false
}

output "cocktail_mcp_url" {
  description = "URL of the Cocktail MCP server"
  value       = google_cloud_run_v2_service.cocktail_mcp_server.uri
}

output "weather_mcp_url" {
  description = "URL of the Weather MCP server"
  value       = google_cloud_run_v2_service.weather_mcp_server.uri
}

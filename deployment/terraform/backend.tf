terraform {
  backend "gcs" {
    bucket = "dw-genai-prod-terraform-state"
    prefix = "a2a-multiagent-langgraph-cicd/prod"
  }
}

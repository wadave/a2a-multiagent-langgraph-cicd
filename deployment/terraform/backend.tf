terraform {
  backend "gcs" {
    bucket = "dw-genai-prod-terraform-state"
    prefix = "a2a-on-ae-multiagent-langgraph/prod"
  }
}

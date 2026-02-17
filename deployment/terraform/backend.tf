terraform {
  backend "gcs" {
    # bucket and prefix are configured via -backend-config in CI/CD
    # For local development, override with:
    #   terraform init -backend-config="bucket=YOUR_PROJECT_ID-terraform-state" -backend-config="prefix=a2a-multiagent-langgraph-cicd/dev"
  }
}

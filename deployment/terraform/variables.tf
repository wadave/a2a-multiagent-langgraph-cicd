variable "staging_project_id" {
  description = "GCP project ID for the staging environment"
  type        = string
}

variable "prod_project_id" {
  description = "GCP project ID for the production environment"
  type        = string
}

variable "cicd_runner_project_id" {
  description = "GCP project ID where CI/CD runners execute"
  type        = string
}

variable "region" {
  description = "GCP region for resource deployment"
  type        = string
  default     = "us-central1"
}

variable "repository_name" {
  description = "GitHub repository name"
  type        = string
}

variable "repository_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "create_repository" {
  description = "Whether to create the GitHub repository"
  type        = bool
  default     = false
}

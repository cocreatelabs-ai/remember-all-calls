variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "call-analyzer"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "callanalyzer"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
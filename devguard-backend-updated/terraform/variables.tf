# terraform/variables.tf
# =======================
# Input variables for the Terraform configuration.
# Values are provided via:
# 1. terraform.tfvars file (gitignored)
# 2. TF_VAR_xxx environment variables
# 3. terraform apply -var="key=value"

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 AMI ID (region-specific — find in AWS console)"
  type        = string
  default     = "ami-0c7217cdde317cfec"  # us-east-1 Ubuntu 22.04 LTS
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"  # Free tier eligible
}

variable "key_pair_name" {
  description = "Name of the AWS EC2 key pair for SSH access"
  type        = string
}

variable "github_repo" {
  description = "GitHub repo path (e.g., yourusername/devguard)"
  type        = string
}

variable "secret_key" {
  description = "Flask SECRET_KEY — use a strong random string in production"
  type        = string
  sensitive   = true  # Won't be shown in terraform output
}

variable "jwt_secret_key" {
  description = "JWT_SECRET_KEY — use a strong random string in production"
  type        = string
  sensitive   = true
}

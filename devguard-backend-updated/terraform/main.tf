# terraform/main.tf
# ===================
# Infrastructure as Code for deploying DevGuard to AWS EC2
#
# WHY TERRAFORM?
# - Instead of clicking through AWS Console (error-prone, not repeatable),
#   we describe infrastructure as code.
# - Running `terraform apply` creates the exact same environment every time.
# - Running `terraform destroy` tears it all down cleanly.
# - Changes are version-controlled in Git — you can see what changed and when.
#
# WHAT THIS CREATES:
# - 1 EC2 instance (t2.micro = free tier eligible)
# - 1 Security Group (firewall rules)
# - Docker installed via user_data script
# - DevGuard API running in a container
#
# HOW TO USE:
#   cd terraform/
#   terraform init          # Download AWS provider
#   terraform plan          # Preview what will be created
#   terraform apply         # Create the infrastructure
#   terraform output        # See the public IP
#   terraform destroy       # Tear down everything

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── AWS Provider Configuration ────────────────────────────────────
provider "aws" {
  region = var.aws_region
  # Credentials come from:
  # 1. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars
  # 2. ~/.aws/credentials file
  # NEVER hardcode credentials in Terraform files
}

# ── Security Group ────────────────────────────────────────────────
# A security group is a virtual firewall for the EC2 instance.
# We define what traffic is allowed IN (ingress) and OUT (egress).
resource "aws_security_group" "devguard_sg" {
  name        = "devguard-security-group"
  description = "DevGuard API security group"

  # Allow SSH for maintenance (in production, restrict to your IP)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict to your IP in production!
  }

  # Allow Flask API traffic
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow Grafana traffic
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic (needed for docker pull, pip install, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "devguard-sg"
    Project = "DevGuard"
  }
}

# ── EC2 Instance ──────────────────────────────────────────────────
resource "aws_instance" "devguard" {
  ami           = var.ami_id           # Ubuntu 22.04 (region-specific)
  instance_type = var.instance_type    # t2.micro = free tier

  vpc_security_group_ids = [aws_security_group.devguard_sg.id]
  key_name               = var.key_pair_name

  # user_data runs once when the instance first boots.
  # We use it to install Docker and start the DevGuard stack.
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Update system
    apt-get update -y
    apt-get install -y docker.io docker-compose-plugin curl git

    # Start Docker service
    systemctl start docker
    systemctl enable docker

    # Add ubuntu user to docker group
    usermod -aG docker ubuntu

    # Clone and start DevGuard
    git clone https://github.com/${var.github_repo}.git /opt/devguard
    cd /opt/devguard

    # Set environment variables
    export SECRET_KEY="${var.secret_key}"
    export JWT_SECRET_KEY="${var.jwt_secret_key}"
    export FLASK_ENV=production

    # Start the full stack
    docker compose up -d --build

    echo "DevGuard deployment complete!"
  EOF

  tags = {
    Name    = "devguard-server"
    Project = "DevGuard"
    Env     = "production"
  }
}

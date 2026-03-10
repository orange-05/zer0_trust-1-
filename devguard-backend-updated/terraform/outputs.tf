# terraform/outputs.tf
# After `terraform apply`, these values are printed.
# Use them to find your deployed server.

output "server_public_ip" {
  description = "Public IP address of the DevGuard server"
  value       = aws_instance.devguard.public_ip
}

output "api_url" {
  description = "DevGuard API URL"
  value       = "http://${aws_instance.devguard.public_ip}:5000"
}

output "grafana_url" {
  description = "Grafana Dashboard URL"
  value       = "http://${aws_instance.devguard.public_ip}:3000"
}

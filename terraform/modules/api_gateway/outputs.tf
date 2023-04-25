output "rest_api_id" {
  value = aws_api_gateway_rest_api.koti.id
  description = "API Gateway REST API ID"
}

output "invoke_url" {
  description = "The URL to invoke the API Gateway"
  value       = aws_api_gateway_deployment.koti_deployment.invoke_url
}




output "raspberry_pi_api_key" {
  description = "API key for Raspberry Pi to access the API Gateway"
  value       = aws_api_gateway_api_key.raspberry_pi_key.value
  sensitive  = true
}
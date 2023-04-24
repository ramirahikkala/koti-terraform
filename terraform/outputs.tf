output "api_gateway_invoke_url" {
  description = "The URL to invoke the API Gateway"
  value       = module.api_gateway.invoke_url
}

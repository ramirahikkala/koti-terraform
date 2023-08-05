
output "telegram_bot_lambda_invoke_arn" {
  description = "The ARN to be used for invoking the insert_ruuvi_data Lambda function from API Gateway"
  value       = aws_lambda_function.telegram_bot.invoke_arn
}

output "python_dependencies_layer_arn" {
  description = "The ARN to be used for invoking the insert_ruuvi_data Lambda function from API Gateway"
  value       = aws_lambda_layer_version.requests_layer.arn
}

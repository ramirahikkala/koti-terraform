
output "insert_ruuvi_data_lambda_invoke_arn" {
  description = "The ARN to be used for invoking the insert_ruuvi_data Lambda function from API Gateway"
  value       = aws_lambda_function.insert_ruuvi_data_lambda.invoke_arn
}


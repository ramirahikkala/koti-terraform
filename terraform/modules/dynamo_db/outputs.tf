output "ruuvi_table_arn" {
  description = "The ARN of the DynamoDB table for Ruuvi data."
  value       = aws_dynamodb_table.ruuvi.arn
}

output "ruuvi_config_table_arn" {
  description = "The ARN of the DynamoDB table for Ruuvi data."
  value       = aws_dynamodb_table.ruuvi_configuration.arn
}

output "ruuvi_subscribers_table_arn" {
  description = "The ARN of the DynamoDB table for Ruuvi data."
  value       = aws_dynamodb_table.subscribers.arn
}

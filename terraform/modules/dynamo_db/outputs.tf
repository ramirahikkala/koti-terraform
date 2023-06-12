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

output "ruuvi_measurement_stats_table_arn" {
  description = "The ARN of the DynamoDB table for Ruuvi data."
  value       = aws_dynamodb_table.measurement_stats.arn
}

output "shelly_devices_table_arn" {
  description = "The ARH of the DynamoDB table for Shelly devices."
  value       = aws_dynamodb_table.shelly_devices.arn
}
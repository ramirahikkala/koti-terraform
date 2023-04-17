output "ruuvi_table_arn" {
  description = "The ARN of the DynamoDB table for Ruuvi data."
  value       = aws_dynamodb_table.ruuvi.arn
}

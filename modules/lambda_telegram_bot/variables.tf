variable "telegram_token" {
  description = "The Telegram bot token"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}

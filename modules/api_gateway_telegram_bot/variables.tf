variable "common_tags" {
  type        = map(string)
  description = "Common tags for resources"
}

variable "telegram_bot_invoke_arn" {
  description = "ARN of the Lambda function to be invoked by the Telegram bot API"
  type        = string
}

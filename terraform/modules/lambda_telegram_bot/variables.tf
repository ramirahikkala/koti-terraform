variable "telegram_token" {
  description = "The Telegram bot token"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}

variable "ruuvi_config_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}
variable "ruuvi_subscribers_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}

variable "timezone" {
  description = "The timezone to use for the bot"
  type        = string
}

variable "shelly_auth" {
  description = "The Shelly auth token"
  type        = string
}
variable "shelly_url" {
  description = "The Shelly URL"
  type        = string
}

variable "ruuvi_measurement_stats_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}
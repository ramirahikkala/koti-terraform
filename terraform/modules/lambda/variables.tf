variable rest_api_id {
  type        = string
  description = "API Gateway REST API ID"
}

variable "dynamodb_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}

variable "ruuvi_config_table_arn" {
  description = "The ARN of the DynamoDB table to grant access to."
  type        = string
}
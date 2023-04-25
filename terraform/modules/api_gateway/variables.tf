variable "common_tags" {
  type        = map(string)
  description = "Common tags for resources"
}

variable "insert_ruuvi_data_lambda_invoke_arn" {
  description = "The ARN to be used for invoking the insert_ruuvi_data Lambda function from API Gateway"
  type        = string
}

variable "get_latest_ruuvi_data_lambda_invoke_arn" {
  description = "The ARN to be used for invoking the insert_ruuvi_data Lambda function from API Gateway"
  type        = string
}
  

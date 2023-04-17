variable "common_tags" {
  type        = map(string)
  description = "Common tags for resources"
}

variable lambda_arn {
  type        = string
  description = "ARN of the Lambda function"
}

variable "lambda_function_name" {
  type        = string
  description = "Name of the Lambda function to integrate with API Gateway"
}

variable "insert_ruuvi_data_lambda_invoke_arn" {
  description = "The ARN to be used for invoking the insert_ruuvi_data Lambda function from API Gateway"
  type        = string
}

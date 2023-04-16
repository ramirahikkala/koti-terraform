output "lambda_arn" {
  value = aws_lambda_function.koti_hello_lambda.arn
  description = "ARN of the Lambda function"
}

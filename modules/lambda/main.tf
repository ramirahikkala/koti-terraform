data "aws_region" "current" {}

data "aws_caller_identity" "current" {}


resource "aws_lambda_function" "koti_hello_lambda" {
  filename      = "hello_lambda.zip"
  function_name = "koti-hello-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "hello_lambda.handler"
  runtime       = "python3.9"

  environment {
    variables = {
      MESSAGE = "hello"
    }
  }
}

resource "aws_lambda_permission" "koti_hello_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.koti_hello_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.rest_api_id}/*/GET/hello"
}


data "archive_file" "hello_lambda" {
  type        = "zip"
  output_path = "hello_lambda.zip"
  source_dir  = "./hello_lambda"
}

resource "aws_iam_role" "lambda_role" {
  name = "koti_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}




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

resource "aws_lambda_function" "insert_ruuvi_data_lambda" {
  function_name = "insert_ruuvi_data"
  handler       = "insert_ruuvi_data.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"

  filename         = data.archive_file.insert_ruuvi_data_lambda.output_path
  source_code_hash = data.archive_file.insert_ruuvi_data_lambda.output_base64sha256
}

data "archive_file" "insert_ruuvi_data_lambda" {
  type        = "zip"
  source_file = "insert_ruuvi_data_lambda/insert_ruuvi_data.py"
  output_path = "insert_ruuvi_data_lambda/insert_ruuvi_data.zip"
}

resource "aws_lambda_permission" "insert_ruuvi_data_lambda_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.insert_ruuvi_data_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.rest_api_id}/*/POST/insert-data"
}


data "aws_iam_policy_document" "dynamodb_policy" {
  statement {
    actions = [
      "dynamodb:PutItem",
    ]
    resources = [
      var.dynamodb_table_arn,
    ]
  }
}


resource "aws_iam_role_policy" "dynamodb_policy" {
  name   = "DynamoDBAccessPolicy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.dynamodb_policy.json
}



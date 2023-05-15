data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

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
  environment {
    variables = {
      TZ = var.timezone
    }
  }
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


resource "aws_lambda_function" "get_latest_ruuvi_data_lambda" {
  function_name = "get_latest_ruuvi_data"
  handler       = "get_latest_ruuvi_data.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.8"

  filename         = data.archive_file.get_latest_ruuvi_data_lambda.output_path
  source_code_hash = data.archive_file.get_latest_ruuvi_data_lambda.output_base64sha256
}

data "archive_file" "get_latest_ruuvi_data_lambda" {
  type        = "zip"
  source_file = "get_latest_ruuvi_data_lambda/get_latest_ruuvi_data.py"
  output_path = "get_latest_ruuvi_data_lambda/get_latest_ruuvi_data.zip"
}

resource "aws_lambda_permission" "get_latest_ruuvi_data_lambda_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_latest_ruuvi_data_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.rest_api_id}/*/GET/ruuvi-data"
}

data "aws_iam_policy_document" "dynamodb_get_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      var.dynamodb_table_arn,
      var.ruuvi_config_table_arn
    ]
  }
}

resource "aws_iam_role_policy" "dynamodb_get_policy" {
  name   = "DynamoDBGetAccessPolicy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.dynamodb_get_policy.json
}


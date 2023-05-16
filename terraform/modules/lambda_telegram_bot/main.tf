resource "aws_lambda_function" "telegram_bot" {
  function_name    = "telegram_bot"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 10
  memory_size      = 128

  role             = aws_iam_role.lambda_execution_role.arn
  filename         = data.archive_file.telegram_bot_lambda.output_path

  source_code_hash = data.archive_file.telegram_bot_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.requests_layer.arn]

  environment {
    variables = {
      TELEGRAM_TOKEN = var.telegram_token,
      TZ = var.timezone
    }
  }
}


resource "aws_iam_role" "lambda_execution_role" {
  name = "telegram_bot_lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "telegram_bot_lambda_policy"
  role   = aws_iam_role.lambda_execution_role.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution_role.name
}

data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:UpdateItem"]
    resources = [var.dynamodb_table_arn, var.ruuvi_config_table_arn, var.ruuvi_subscribers_table_arn]
  }
}


data "archive_file" "telegram_bot_lambda" {
  type        = "zip"
  source_dir="src/telegram_bot_lambda/"
  output_path = "deployment_zips/lambda_function.zip"
}

data "archive_file" "request_layer_zip" {
  type        = "zip"
  source_dir="src/lambda_layer/"
  output_path = "deployment_zips/layer.zip"
}

resource "aws_lambda_layer_version" "requests_layer" {
  layer_name = "requests"
  filename   = "layer.zip"
  compatible_runtimes = ["python3.9"]
}

resource "null_resource" "install_requests" {
  provisioner "local-exec" {
    command = "pip install -r src/requirements.txt -t src/lambda_layer/python"
  }

  triggers = {
    requirements = filesha256("src/requirements.txt")
  }
}


resource "aws_lambda_function" "temperature_alarm" {
  function_name    = "temperature_alarm"
  handler          = "temperature_alarm_lambda.lambda_handler"
  runtime          = "python3.9"
  timeout          = 10
  memory_size      = 128

  role             = aws_iam_role.lambda_execution_role.arn
  filename         = data.archive_file.temperature_alarm_lambda.output_path

  source_code_hash = data.archive_file.temperature_alarm_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.requests_layer.arn]
  environment {
    variables = {
      TELEGRAM_TOKEN = var.telegram_token,
      TZ = var.timezone,
      SHELLY_URL = var.shelly_url,
      SHELLY_AUTH = var.shelly_auth
    }
  }
}

data "archive_file" "temperature_alarm_lambda" {
  type        = "zip"
  source_dir="src/temperature_alarm_lambda/"
  output_path = "deployment_zips/temperature_alarm_lambda_function.zip"
}


resource "aws_cloudwatch_event_rule" "every_five_minutes" {
  name                = "every-five-minutes"
  description         = "Fires every five minutes"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "temperature_alarm_lambda" {
  rule      = aws_cloudwatch_event_rule.every_five_minutes.name
  target_id = "temperature_alarm_lambda"
  arn       = aws_lambda_function.temperature_alarm.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.temperature_alarm.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_five_minutes.arn
}


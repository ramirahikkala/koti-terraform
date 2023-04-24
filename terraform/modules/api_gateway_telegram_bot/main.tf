data "aws_region" "current" {}

data "aws_caller_identity" "current" {}


resource "aws_api_gateway_rest_api" "telegram_bot" {
  name = "Telegram Bot API"
}

resource "aws_api_gateway_resource" "telegram_bot_resource" {
  parent_id   = aws_api_gateway_rest_api.telegram_bot.root_resource_id
  path_part   = "telegram-bot"
  rest_api_id = aws_api_gateway_rest_api.telegram_bot.id
}

resource "aws_api_gateway_method" "telegram_bot_post" {
  rest_api_id   = aws_api_gateway_rest_api.telegram_bot.id
  resource_id   = aws_api_gateway_resource.telegram_bot_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "telegram_bot_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.telegram_bot.id
  resource_id = aws_api_gateway_resource.telegram_bot_resource.id
  http_method = aws_api_gateway_method.telegram_bot_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.telegram_bot_invoke_arn
}

resource "aws_api_gateway_deployment" "telegram_bot_deployment" {
  depends_on = [
    aws_api_gateway_integration.telegram_bot_lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.telegram_bot.id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "telegram_bot_stage" {
  rest_api_id   = aws_api_gateway_rest_api.telegram_bot.id
  deployment_id = aws_api_gateway_deployment.telegram_bot_deployment.id
  stage_name    = "v1"
}

output "telegram_bot_invoke_url" {
  value = "${aws_api_gateway_deployment.telegram_bot_deployment.invoke_url}${aws_api_gateway_stage.telegram_bot_stage.stage_name}/telegram-bot"
}

resource "aws_lambda_permission" "allow_api_gateway_telegram_bot" {
  statement_id  = "AllowAPIGatewayInvokeTelegramBot"
  action        = "lambda:InvokeFunction"
  function_name = "telegram_bot"
  principal     = "apigateway.amazonaws.com"

   source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.telegram_bot.id}/*/*"
}
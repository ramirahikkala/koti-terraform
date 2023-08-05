data "aws_region" "current" {}

data "aws_caller_identity" "current" {}


resource "aws_api_gateway_rest_api" "plant_count" {
  name = "Count plants"
}

resource "aws_api_gateway_resource" "plant_count_resource" {
  parent_id   = aws_api_gateway_rest_api.plant_count.root_resource_id
  path_part   = "plants"
  rest_api_id = aws_api_gateway_rest_api.plant_count.id
}

resource "aws_api_gateway_method" "plant_count_post" {
  rest_api_id   = aws_api_gateway_rest_api.plant_count.id
  resource_id   = aws_api_gateway_resource.plant_count_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plant_count_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.plant_count.id
  resource_id = aws_api_gateway_resource.plant_count_resource.id
  http_method = aws_api_gateway_method.plant_count_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.plant_count_invoke_arn
}

resource "aws_api_gateway_deployment" "plant_count_deployment" {
  depends_on = [
    aws_api_gateway_integration.plant_count_lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.plant_count.id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "plant_count_stage" {
  rest_api_id   = aws_api_gateway_rest_api.plant_count.id
  deployment_id = aws_api_gateway_deployment.plant_count_deployment.id
  stage_name    = "v1"
}

output "plant_count_invoke_url" {
  value = "${aws_api_gateway_deployment.plant_count_deployment.invoke_url}${aws_api_gateway_stage.plant_count_stage.stage_name}/telegram-bot"
}

resource "aws_lambda_permission" "allow_api_gateway_plant_count" {
  statement_id  = "AllowAPIGatewayInvokePlantCount"
  action        = "lambda:InvokeFunction"
  function_name = "plant_count_lambda"
  principal     = "apigateway.amazonaws.com"

   source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.plant_count.id}/*/*"
}
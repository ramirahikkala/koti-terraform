data "aws_region" "current" {}

data "aws_caller_identity" "current" {}


resource "aws_api_gateway_rest_api" "koti" {
  name = "Koti Environment Data"
}

resource "aws_api_gateway_resource" "ruuvi_data_resource" {
  parent_id   = aws_api_gateway_rest_api.koti.root_resource_id
  path_part   = "ruuvi-data"
  rest_api_id = aws_api_gateway_rest_api.koti.id
}


resource "aws_api_gateway_method" "post_ruuvi_data" {
  rest_api_id   = aws_api_gateway_rest_api.koti.id
  resource_id   = aws_api_gateway_resource.ruuvi_data_resource.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = true
}


resource "aws_api_gateway_integration" "post_ruuvi_data_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  resource_id = aws_api_gateway_resource.ruuvi_data_resource.id
  http_method = aws_api_gateway_method.post_ruuvi_data.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.insert_ruuvi_data_lambda_invoke_arn
}

resource "aws_api_gateway_deployment" "koti_deployment" {
  depends_on = [
    aws_api_gateway_integration.post_ruuvi_data_lambda_integration,
    aws_api_gateway_integration.get_latest_ruuvi_data_lambda_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.koti.id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "koti_stage" {
  rest_api_id   = aws_api_gateway_rest_api.koti.id
  deployment_id = aws_api_gateway_deployment.koti_deployment.id
  stage_name    = "v1"
}


output "koti_url" {
  value = "${aws_api_gateway_deployment.koti_deployment.invoke_url}${aws_api_gateway_stage.koti_stage.stage_name}/ruuvi-data"
}


resource "aws_api_gateway_api_key" "raspberry_pi_key" {
  name = "raspberry-pi-key"
}

resource "aws_api_gateway_usage_plan" "raspberry_pi_usage_plan" {
  name        = "RaspberryPiUsagePlan"
  description = "Usage plan for Raspberry Pi"

  api_stages {
    api_id = aws_api_gateway_rest_api.koti.id
    stage  = aws_api_gateway_stage.koti_stage.stage_name
  }
}


resource "aws_api_gateway_usage_plan_key" "raspberry_pi_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.raspberry_pi_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.raspberry_pi_usage_plan.id
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "insert_ruuvi_data"
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.koti.id}/*/*"
}

resource "aws_api_gateway_method" "get_latest_ruuvi_data" {
  rest_api_id   = aws_api_gateway_rest_api.koti.id
  resource_id   = aws_api_gateway_resource.ruuvi_data_resource.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "get_latest_ruuvi_data_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  resource_id = aws_api_gateway_resource.ruuvi_data_resource.id
  http_method = aws_api_gateway_method.get_latest_ruuvi_data.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.get_latest_ruuvi_data_lambda_invoke_arn
}

resource "aws_api_gateway_deployment" "get_latest_ruuvi_data_deployment" {
  depends_on = [
    aws_api_gateway_integration.get_latest_ruuvi_data_lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.koti.id

  lifecycle {
    create_before_destroy = true
  }
}


data "aws_region" "current" {}


resource "aws_api_gateway_rest_api" "koti" {
  name = "Koti Environment Data"
}

resource "aws_api_gateway_resource" "koti_hello_resource" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  parent_id   = aws_api_gateway_rest_api.koti.root_resource_id
  path_part   = "hello"
}

resource "aws_api_gateway_method" "koti_hello_get" {
  rest_api_id   = aws_api_gateway_rest_api.koti.id
  resource_id   = aws_api_gateway_resource.koti_hello_resource.id
  http_method   = "GET"
  authorization = "NONE"
}


resource "aws_api_gateway_integration" "koti_hello_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  resource_id = aws_api_gateway_resource.koti_hello_resource.id
  http_method = aws_api_gateway_method.koti_hello_get.http_method
  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri  = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.lambda_arn}/invocations"

}

resource "aws_api_gateway_deployment" "koti_hello_deployment" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  depends_on = [aws_api_gateway_integration.koti_hello_lambda_integration]
  triggers = {
    redeployment_lambda = sha1(jsonencode(var.lambda_function_name))
  }


  lifecycle {
    create_before_destroy = true
  }
}


output "koti_hello_url" {
  value = "${aws_api_gateway_deployment.koti_hello_deployment.invoke_url}${aws_api_gateway_stage.koti_hello_test_stage.stage_name}${aws_api_gateway_resource.koti_hello_resource.path}"
}


resource "aws_api_gateway_stage" "koti_hello_test_stage" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  deployment_id = aws_api_gateway_deployment.koti_hello_deployment.id
  stage_name = "example-stage"
}


resource "aws_api_gateway_resource" "insert_data_resource" {
  parent_id   = aws_api_gateway_rest_api.koti.root_resource_id
  path_part   = "insert-data"
  rest_api_id = aws_api_gateway_rest_api.koti.id
}

resource "aws_api_gateway_method" "insert_data_post" {
  rest_api_id   = aws_api_gateway_rest_api.koti.id
  resource_id   = aws_api_gateway_resource.insert_data_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "insert_ruuvi_data_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  resource_id = aws_api_gateway_resource.insert_data_resource.id
  http_method = aws_api_gateway_method.insert_data_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.insert_ruuvi_data_lambda_invoke_arn
}


resource "aws_api_gateway_deployment" "insert_ruuvi_data_deployment" {
  depends_on = [
    aws_api_gateway_integration.insert_ruuvi_data_lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.koti.id
  stage_name  = "test"

  lifecycle {
    create_before_destroy = true
  }
}



data "aws_secretsmanager_secret_version" "creds" {
  secret_id = "koti/postgres/admin"
}

locals {
  db_creds = jsondecode(
    data.aws_secretsmanager_secret_version.creds.secret_string
  )
}

resource "aws_db_instance" "postgres" {
  identifier           = "koti"
  allocated_storage    = 10
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "15.2"
  instance_class       = "db.t3.micro"
  db_name              = "koti"
  username             = local.db_creds.username
  password             = local.db_creds.password
  vpc_security_group_ids = [aws_security_group.postgres_db.id]

}

resource "aws_s3_bucket" "koti-terraform-state-bucket" {
  bucket = "koti-terraform-state-bucket"
}

provider "aws" {
  region = "eu-central-1"
}

locals {
  common_tags = {
    Terraform = "true"
    Environment = "production"
  }
}

resource "aws_security_group" "bastion" {
  name        = "bastion"
  description = "Security group for bastion host"
  vpc_id      = "vpc-082b653beb2666db9"
  tags        = local.common_tags

  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  

}

resource "aws_security_group_rule" "bastion_ingress" {
  security_group_id = aws_security_group.bastion.id

  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["85.76.8.133/32"]
}

resource "aws_security_group_rule" "bastion_egress" {
  security_group_id = aws_security_group.bastion.id

  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.postgres_db.id
}

resource "aws_security_group" "postgres_db" {
  name        = "postgres_db"
  description = "Security group for PostgreSQL database"
  vpc_id      = "vpc-082b653beb2666db9"
  tags        = local.common_tags

  
}

resource "aws_security_group_rule" "postgres_db_ingress" {
  security_group_id = aws_security_group.postgres_db.id

  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion.id
}

resource "aws_instance" "bastion" {
  ami           = "ami-0968bb84a3c33d0be"
  instance_type = "t2.micro"
  key_name      = "koti_key"

  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id              = "subnet-002fbd9fbb6278bf0"

  tags = merge(local.common_tags, { Name = "BastionHost" })
}

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

  source_arn = "${aws_api_gateway_rest_api.koti.execution_arn}/*/GET/hello"
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

locals {
  lambda_arn = aws_lambda_function.koti_hello_lambda.arn
  rest_api_id = aws_api_gateway_rest_api.koti.id
}

resource "aws_api_gateway_integration" "koti_hello_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  resource_id = aws_api_gateway_resource.koti_hello_resource.id
  http_method = aws_api_gateway_method.koti_hello_get.http_method
  integration_http_method = "POST"
  type = "AWS_PROXY"
  uri  = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${local.lambda_arn}/invocations"
}

resource "aws_api_gateway_deployment" "koti_hello_deployment" {
  rest_api_id = aws_api_gateway_rest_api.koti.id
  depends_on = [aws_api_gateway_integration.koti_hello_lambda_integration]
  triggers = {
    redeployment_lambda = sha1(jsonencode(aws_lambda_function.koti_hello_lambda))
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


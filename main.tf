provider "aws" {
  region = "eu-central-1"
}

data "aws_secretsmanager_secret_version" "creds" {
  secret_id = "koti/postgres/admin"
}

locals {
  db_creds = jsondecode(
    data.aws_secretsmanager_secret_version.creds.secret_string
  )
  common_tags = {
    Terraform = "true"
    Environment = "production"
  }
}


module "api_gateway" {
  source = "./modules/api_gateway"
  common_tags = local.common_tags
  lambda_arn = module.lambda.lambda_arn
  lambda_function_name = "koti_hello_lambda"
  insert_ruuvi_data_lambda_invoke_arn = module.lambda.insert_ruuvi_data_lambda_invoke_arn
}

module "lambda" {
  source = "./modules/lambda"
  rest_api_id = module.api_gateway.rest_api_id
  dynamodb_table_arn = module.dynamo_db.ruuvi_table_arn
}

module "S3_bucket" {
  source = "./modules/S3_bucket"
}

module "dynamo_db" {
  source = "./modules/dynamo_db"
  common_tags = local.common_tags
}


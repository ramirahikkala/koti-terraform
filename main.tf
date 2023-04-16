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
}

module "lambda" {
  source = "./modules/lambda"
  rest_api_id = module.api_gateway.rest_api_id
}

module "bastion" {
  source = "./modules/bastion"
  common_tags = local.common_tags
  postgres_security_group_id = module.postgres_db.postgres_security_group_id
}

module "postgres_db" {
  source = "./modules/postgres_db"
  username      = local.db_creds.username
  password      = local.db_creds.password
  common_tags   = local.common_tags
  bastion_sg_id = module.bastion.bastion_sg_id
}

module "S3_bucket" {
  source = "./modules/S3_bucket"
}




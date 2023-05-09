provider "aws" {
  region = "eu-central-1"
}

data "aws_secretsmanager_secret_version" "creds" {
  secret_id = "koti/postgres/admin"
}

data "aws_secretsmanager_secret_version" "telegram_bot_secrets" {
  secret_id = "koti/telegram_bot_secrets"
}

locals {
  db_creds = jsondecode(
    data.aws_secretsmanager_secret_version.creds.secret_string
  )
  common_tags = {
    Terraform = "true"
    Environment = "production"
  }
  telegram_bot_secrets = jsondecode(
    data.aws_secretsmanager_secret_version.telegram_bot_secrets.secret_string
  )
}


module "api_gateway" {
  source = "./modules/api_gateway"
  common_tags = local.common_tags
  insert_ruuvi_data_lambda_invoke_arn = module.lambda.insert_ruuvi_data_lambda_invoke_arn
  get_latest_ruuvi_data_lambda_invoke_arn = module.lambda.get_latest_ruuvi_data_lambda_invoke_arn
}

module "lambda" {
  source = "./modules/lambda"
  rest_api_id = module.api_gateway.rest_api_id
  dynamodb_table_arn = module.dynamo_db.ruuvi_table_arn
  ruuvi_config_table_arn = module.dynamo_db.ruuvi_config_table_arn
  timezone = "Europe/Helsinki"
}

module "S3_bucket" {
  source = "./modules/S3_bucket"
}

module "dynamo_db" {
  source = "./modules/dynamo_db"
  common_tags = local.common_tags
}

resource "aws_secretsmanager_secret" "raspberry_pi_api_key" {
  name        = "raspberry_pi_api_key"
  description = "API key for Raspberry Pi to access the API Gateway"
}

resource "aws_secretsmanager_secret_version" "raspberry_pi_api_key" {
  secret_id     = aws_secretsmanager_secret.raspberry_pi_api_key.id
  secret_string = module.api_gateway.raspberry_pi_api_key
}

module "lambda_telegram_bot" {
  source        = "./modules/lambda_telegram_bot"
  telegram_token = local.telegram_bot_secrets.token
  dynamodb_table_arn = module.dynamo_db.ruuvi_table_arn
  ruuvi_config_table_arn = module.dynamo_db.ruuvi_config_table_arn
  ruuvi_subscribers_table_arn = module.dynamo_db.ruuvi_subscribers_table_arn
  timezone = "Europe/Helsinki"
}

module "api_gateway_telegram_bot" {
  source = "./modules/api_gateway_telegram_bot"
  common_tags = local.common_tags
  telegram_bot_invoke_arn = module.lambda_telegram_bot.telegram_bot_lambda_invoke_arn
}
resource "aws_dynamodb_table" "ruuvi" {
  name           = "ruuvi"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "name"
  range_key      = "datetime"

  attribute {
    name = "name"
    type = "S"
  }

  attribute {
    name = "datetime"
    type = "S"
  }

  tags = var.common_tags
}

resource "aws_dynamodb_table" "ruuvi_configuration" {
  name           = "ruuvi_configuration"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "mac"

  attribute {
    name = "mac"
    type = "S"
  }

  tags = var.common_tags
}

resource "aws_dynamodb_table" "subscribers" {
  name           = "ruuvi_subscribers"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "chat_id"

  attribute {
    name = "chat_id"
    type = "N"
  }
}

resource "aws_dynamodb_table" "measurement_stats" {
  name           = "measurement_stats"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "measurement_name"
  range_key      = "statistics_type"

  attribute {
    name = "measurement_name"
    type = "S"
  }

  attribute {
    name = "statistics_type"
    type = "S"
  }

  lifecycle {
    ignore_changes = [
      tags_all
    ]
  }
}


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

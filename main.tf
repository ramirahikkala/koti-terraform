

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
}


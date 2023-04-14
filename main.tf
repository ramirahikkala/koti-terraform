

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

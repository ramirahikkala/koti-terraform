
locals {
  common_tags = var.common_tags
}

resource "aws_db_instance" "postgres" {
  identifier           = "koti"
  allocated_storage    = 10
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "15.2"
  instance_class       = "db.t3.micro"
  db_name              = "koti"
  username             = var.username
  password             = var.password
  vpc_security_group_ids = [aws_security_group.postgres_db.id]

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
  source_security_group_id = var.bastion_sg_id
}

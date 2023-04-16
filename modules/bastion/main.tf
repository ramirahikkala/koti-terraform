locals {
  common_tags = var.common_tags
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
  source_security_group_id = var.postgres_security_group_id
}



resource "aws_instance" "bastion" {
  ami           = "ami-0968bb84a3c33d0be"
  instance_type = "t2.micro"
  key_name      = "koti_key"

  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id              = "subnet-002fbd9fbb6278bf0"

  tags = merge(local.common_tags, { Name = "BastionHost" })
}


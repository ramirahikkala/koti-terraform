terraform {
  backend "s3" {
    bucket         = "koti-terraform-state-bucket"
    key            = "terraform.tfstate"
    encrypt        = true
    region         = "eu-central-1"
  }
}

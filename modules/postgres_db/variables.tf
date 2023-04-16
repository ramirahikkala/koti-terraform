variable "username" {
  type        = string
  description = "Username for PostgreSQL database" 
}
variable "password" {
  type        = string
  description = "Password for PostgreSQL database" 
}
variable "common_tags" {
  type        = map(string)
  description = "Common tags for resources"
}

variable "bastion_sg_id" {
  description = "Bastion security group ID"
  type        = string
}


variable "common_tags" {
  type        = map(string)
  description = "Common tags for resources"
}

variable "postgres_security_group_id" {
  type        = string
  description = "The ID of the Postgres security group."
}


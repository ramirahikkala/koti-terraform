# koti-terraform
Terraform for my home things


# Instructions

Create ssh tunnel to the server:

```ssh -i ~/.ssh/koti_keys.pem -L localhost:5432:koti.cmkg76o4grmk.eu-central-1.rds.amazonaws.com:5432  ubuntu@18.156.163.254```

Connect to the database:

```psql -h localhost -p 5432 -U rami koti```

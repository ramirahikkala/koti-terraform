# Home Automation Project

This project is a home automation system that combines several services to manage and control different aspects of a smart home. It consists of the following components:

A RuuviTag sensor for measuring temperature, humidity, and air pressure
An AWS infrastructure for processing and storing the sensor data
A Telegram bot for interacting with the system and receiving notifications
The project is organized into two main directories:

## Ansible 

Contains Ansible playbooks for configuring the Raspberry Pi
terraform: Contains Terraform configurations for provisioning AWS resources
Ansible
The ansible directory contains the Ansible playbooks and configuration files for setting up the Raspberry Pi. It installs the necessary software, configures the system, and sets up the scripts for collecting RuuviTag sensor data.


## Terraform
The terraform directory contains the Terraform configuration files for provisioning the AWS infrastructure. It includes AWS Lambda functions, an API Gateway, a DynamoDB table, and an S3 bucket.

To deploy the infrastructure to a new environment, you need to initialize and apply the Terraform configuration:

```sh
cd terraform
terraform init
terraform apply
```

## AWS Lambda Functions
- insert_ruuvi_data_lambda: Processes the RuuviTag sensor data and stores it in a DynamoDB table.
- telegram_bot_lambda: Handles incoming messages and commands from the Telegram bot.
- temperature_alarm_lambda: Monitors the temperature data and sends alerts via the Telegram bot if the temperature exceeds a defined threshold.
## AWS Resources
The project uses several AWS resources, which are organized into Terraform modules:

- api_gateway: An Amazon API Gateway for receiving sensor data from the Raspberry Pi and forwarding it to the insert_ruuvi_data_lambda function.
api_gateway_telegram_bot: An Amazon API Gateway for receiving updates from the Telegram bot and forwarding them to the telegram_bot_lambda function.
- dynamo_db: An Amazon DynamoDB table for storing the RuuviTag sensor data.
lambda: A generic module for creating AWS Lambda functions.
lambda_telegram_bot: A module for creating the telegram_bot_lambda function.
- S3_bucket: An Amazon S3 bucket for storing the terraform backend data

# Ruuvi Data API

## Endpoints

### 1. Create a new Ruuvi data entry

- Method: `POST`
- Path: `/v1/ruuvi-data`
- Request: JSON payload with Ruuvi data (datetime, name, temperature, temperature_calibrated, humidity, pressure)
- Response: `201 Created` (if successful), with the created data entry and a unique ID (e.g., UUID)

### 2. Retrieve a list of Ruuvi data entries

- Method: `GET`
- Path: `/v1/ruuvi-data`
- Response: `200 OK`, with an array of Ruuvi data entries, including the unique ID for each entry

### 3. Retrieve a specific Ruuvi data entry by its unique ID

- Method: `GET`
- Path: `/v1/ruuvi-data/{id}`
- Response: `200 OK`, with the requested Ruuvi data entry, or `404 Not Found` if the entry does not exist

### 4. Update a specific Ruuvi data entry by its unique ID

- Method: `PUT`
- Path: `/v1/ruuvi-data/{id}`
- Request: JSON payload with updated Ruuvi data
- Response: `200 OK` if the entry was updated successfully, or `404 Not Found` if the entry does not exist

### 5. Delete a specific Ruuvi data entry by its unique ID

- Method: `DELETE`
- Path: `/v1/ruuvi-data/{id}`
- Response: `204 No Content` if the entry was deleted successfully, or `404 Not Found` if the entry does not exist

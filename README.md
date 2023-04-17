# koti-terraform
Terraform for my home things


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

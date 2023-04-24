import json
import requests
import time
from decimal import Decimal
from datetime import datetime, timedelta
from ruuvitag_sensor.ruuvi import RuuviTagSensor
import os

api_url = "https://ckslcpsx8d.execute-api.eu-central-1.amazonaws.com/v1/ruuvi-data"
API_KEY = os.environ.get("RUUVI_API_KEY")

throttle_interval = timedelta(minutes=5)
last_sent = {}

def handle_data(found_data):
    mac = found_data[0]
    data = found_data[1]
    now = datetime.utcnow()

    if mac not in last_sent or now - last_sent[mac] >= throttle_interval:
        # Calibrate temperature if needed
        temperature_calibrated = data['temperature']  # Replace this line with calibration logic if r>

        payload = {
            'name': mac,
            'temperature': str(data['temperature']),
            'temperature_calibrated': str(temperature_calibrated),
            'humidity': str(data['humidity']),
            'pressure': str(data['pressure'])
        }
        print("Sending: " + str(payload))

        response = send_to_api(payload)
        print(response)

        # Update the last sent timestamp for the current MAC address
        last_sent[mac] = now

def send_to_api(payload):
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': API_KEY
        }
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Data inserted successfully'})}
        else:
            return {'statusCode': response.status_code, 'body': json.dumps({'message': 'Error inserting data'})}
    
    except Exception as e:
        print(e)
        return {'statusCode': 400, 'body': json.dumps({'message': 'Error sending data to API'})}

if __name__ == "__main__":
    print("Starting to listen for the ruuvi data")
    RuuviTagSensor.get_data(handle_data)
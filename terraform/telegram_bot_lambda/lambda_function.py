import json
import logging
import boto3
from boto3.dynamodb.conditions import Key
import requests
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/'

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')

def get_configuration():
    dynamodb = boto3.resource('dynamodb')
    config_table = dynamodb.Table('ruuvi_configuration')
    response = config_table.scan()
    data = response['Items']
    config = {}
    for item in data:
        mac = item['mac']
        config[mac] = {
            'name': item['name'],
            'temperatureOffset': item.get('temperatureOffset', 0),
            'temperatureMonitoring_high': item.get('temperatureMonitoring_high', None),
            'temperatureMonitoring_low': item.get('temperatureMonitoring_low', None)
        }
    return config


def get_distinct_names():
    response = table.scan(
        ProjectionExpression="#name",
        ExpressionAttributeNames={
            "#name": "name"
        }
    )

    data = response['Items']
    names = set()

    for item in data:
        names.add(item['name'])

    return names


def get_latest_measurement(mac, config):
    response = table.query(
        KeyConditionExpression=Key('name').eq(mac),
        ScanIndexForward=False, # Sort by datetime in descending order
        Limit=1
    )
    if(response['Items']):
        item = response['Items'][0]
        dt = datetime.strptime(item['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        temp = float(item['temperature']) + float(config[mac]['temperatureOffset'])
        return {'datetime': dt, 'temperature': temp}
    return None



def get_latest_temperatures():
    config = get_configuration()
    latest_temps = {}
    for mac, data in config.items():
        measurement = get_latest_measurement(mac, config)
        if measurement is not None:
            latest_temps[data["name"]] = measurement
    return latest_temps


def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"An error occurred sending the message: {e}")

def process_update(update):
    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    
    if text == "/temps":
        latest_temps = get_latest_temperatures()
        response_text = "Lämpötilat:\n"

        for name, data in latest_temps.items():
            dt = data['datetime']
            temp = data['temperature']
            response_text += f"{name}: {temp}°C"

            # Check if the data is older than 5 minutes
            now = datetime.utcnow()
            if (now - dt) > timedelta(minutes=5):
                age = now - dt
                response_text += f" (Vanhentunut {age.seconds // 60} minuuttia sitten)"

            response_text += "\n"

        send_message(chat_id, response_text)

def lambda_handler(event, context):
    try:        

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.info(f'Event Body: {json.dumps(event)}')

        update = json.loads(event["body"])
        process_update(update)

        return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"result": "Success"})
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"result": "Error processing update"})
        }




import json
import requests
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import os
import traceback

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SUBSCRIPTION_TABLE_NAME = 'ruuvi_subscribers'

dynamodb = boto3.resource('dynamodb')
config_table = dynamodb.Table('ruuvi_configuration')
data_table = dynamodb.Table('ruuvi')
dynamodb_subscriber = boto3.resource('dynamodb')
subscriber_table = dynamodb_subscriber.Table(SUBSCRIPTION_TABLE_NAME)

def get_subscribers():
    response = subscriber_table.scan()
    data = response['Items']
    subscribers = [item['chat_id'] for item in data]
    return subscribers

def get_configuration():
    response = config_table.scan()
    data = response['Items']
    config = {}
    for item in data:
        mac = item['mac']
        config[mac] = {
            'name': item['name'],
            'temperatureOffset': item.get('temperatureOffset', 0),
            'temperatureMonitoring_high': item.get('temperatureMonitoring_high', None),
            'temperatureMonitoring_low': item.get('temperatureMonitoring_low', None),
            'temperatureMonitoring_critical_low': item.get('temperatureMonitoring_critical_low', None),
            'temperatureMonitoring_critical_high': item.get('temperatureMonitoring_critical_high', None),
            'lastAlarmState': item.get('lastAlarmState', None),
        }
    return config


def update_alarm_state(mac, state):
    response = config_table.update_item(
        Key={
            'mac': mac,
        },
        UpdateExpression="set lastAlarmState=:s",
        ExpressionAttributeValues={
            ':s': state
        },
        ReturnValues="UPDATED_NEW"
    )

def get_latest_measurement(mac):
    response = data_table.query(
        KeyConditionExpression=Key('name').eq(mac),
        ScanIndexForward=False,  # Sort by datetime in descending order
        Limit=1
    )
    if response['Items']:
        item = response['Items'][0]
        dt = datetime.strptime(item['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        temp = item['temperature']
        return {'datetime': dt, 'temperature': temp}
    return None

def is_daytime():
    now = datetime.now()
    return now.hour >= 8 and now.hour <= 22

def check_temperature_limits():
    
    config = get_configuration()
    
    subscribers = get_subscribers()
    

    for mac, config_data in config.items():
        
        # Get the latest temperature measurement for the current name
        latest_measurement = get_latest_measurement(mac)

        if latest_measurement:
            calibrated_temperature = float(latest_measurement['temperature']) + float(config_data['temperatureOffset'])
            high_limit = float(config_data['temperatureMonitoring_high']) if config_data['temperatureMonitoring_high'] is not None else None
            low_limit = float(config_data['temperatureMonitoring_low']) if config_data['temperatureMonitoring_low'] is not None else None
            critical_low_limit = float(config_data['temperatureMonitoring_critical_low']) if config_data['temperatureMonitoring_critical_low'] is not None else None
            critical_high_limit = float(config_data['temperatureMonitoring_critical_high']) if config_data['temperatureMonitoring_critical_high'] is not None else None
            last_alarm_state = config_data['lastAlarmState']

            alarm_triggered = False
            message = ""

            if critical_high_limit is not None and calibrated_temperature > critical_high_limit:
                if last_alarm_state != 'CRITICAL_HIGH':
                    message = f"Cricital temperature alarm: {config_data['name']} is too high ({calibrated_temperature}°C)"
                    update_alarm_state(mac, 'CRITICAL_HIGH')
                    alarm_triggered = True
            elif critical_low_limit is not None and calibrated_temperature < critical_low_limit:
                if last_alarm_state != 'CRITICAL_LOW':
                    message = f"Critical temperature alarm: {config_data['name']} is too low ({calibrated_temperature}°C)"
                    update_alarm_state(mac, 'CRITICAL_LOW')
                    alarm_triggered = True
            elif is_daytime():
                if high_limit is not None and calibrated_temperature > high_limit:
                    if last_alarm_state != 'HIGH' and last_alarm_state != 'CRITICAL_HIGH':
                        message = f"Temperature alarm: {config_data['name']} is too high ({calibrated_temperature}°C)"
                        update_alarm_state(mac, 'HIGH')
                        alarm_triggered = True

                elif low_limit is not None and calibrated_temperature < low_limit:
                    if last_alarm_state != 'LOW' and last_alarm_state != 'CRITICAL_LOW':
                        message = f"Temperature alarm: {config_data['name']} is too low ({calibrated_temperature}°C)"
                        update_alarm_state(mac, 'LOW')
                        alarm_triggered = True

                elif last_alarm_state is not None:
                    message = f"Temperature back to normal: {config_data['name']} ({calibrated_temperature}°C)"
                    update_alarm_state(mac, None)
                    alarm_triggered = True

            if alarm_triggered:
                for chat_id in subscribers:
                    send_telegram_message(chat_id, message)

def send_telegram_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(TELEGRAM_API_URL, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"An error occurred sending the message: {e}")

def lambda_handler(event, context):
    print("Running handler")
    try:
        check_temperature_limits()
        print("Returining from handler")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Temperature check completed'})}
    except Exception as e:
            print("Exception occurred:")
            print(str(e))
            print(traceback.format_exc())  # Print the complete traceback information
            return {'statusCode': 500, 'body': json.dumps({'message': 'Error checking temperature limits'})}

if __name__ == "__main__":
    lambda_handler(None, None)


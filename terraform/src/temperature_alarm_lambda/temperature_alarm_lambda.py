import json
import requests
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
import os
import traceback

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SHELLY_URL = os.environ.get('SHELLY_URL')
SHELLY_AUTH = os.environ.get('SHELLY_AUTH')
SUBSCRIPTION_TABLE_NAME = 'ruuvi_subscribers'

dynamodb = boto3.resource('dynamodb')
config_table = dynamodb.Table('ruuvi_configuration')
data_table = dynamodb.Table('ruuvi')
stats_table = dynamodb.Table('measurement_stats')
subscriber_table = dynamodb.Table(SUBSCRIPTION_TABLE_NAME)

def set_last24h_min_max():
    config = get_configuration()
    for mac, config_data in config.items():
        name = config_data['name']
        response = data_table.query(
        KeyConditionExpression=Key('name').eq(name) & Key('datetime').between(str(datetime.datetime.utcnow() - timedelta(days=1)), str(datetime.datetime.utcnow())),
        )

        items = response['Items']
        # Sort by temperature
        items.sort(key=lambda x: float(x['temperature_calibrated']))
        # Get min and max
        min = items[0]
        max = items[-1]

        stats_item = {
            'measurement_name': name,
            'statistics_type': 'past24h',
            'temperature': {                
                'min': { 'value': min['temperature_calibrated'], 'datetime': min['datetime'] },
                'max': { 'value': max['temperature_calibrated'], 'datetime': max['datetime'] },

            },
        }

        response = stats_table.put_item(Item=stats_item)
        

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
        
        if 'alarms' not in item:
            item['alarms'] = {}
        
        if 'deviceActions' not in item:
            item['deviceActions'] = []

        config[mac] = {
            'name': item['name'],
            'temperatureOffset': item.get('temperatureOffset', 0),
            'lastAlarmState': item.get('lastAlarmState', True),
            'alarms': {
                'critical_low': item['alarms'].get('critical_low', None),
                'critical_high': item['alarms'].get('critical_high', None),
                'high': item['alarms'].get('high', None),
                'low': item['alarms'].get('low', None),
            },
            'deviceActions': [
                {
                    'on_low': deviceAction.get('on_low', None),
                    'off_low': deviceAction.get('off_low', None),
                    'on_high': deviceAction.get('on_high', None),
                    'off_high': deviceAction.get('off_high', None),
                    'device_id': deviceAction.get('device_id', None)
                }
                for deviceAction in item.get('deviceActions', [])
            ]
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

def get_latest_measurement(name):
    response = data_table.query(
        KeyConditionExpression=Key('name').eq(name),
        ScanIndexForward=False,  # Sort by datetime in descending order
        Limit=1
    )
    if(response['Items']):
        item = response['Items'][0]
        dt = datetime.strptime(item['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        temp = item['temperature_calibrated']
        return {'datetime': dt, 'temperature_calibrated': temp}
    return None

def is_daytime():
    now = datetime.now()
    return now.hour >= 8 and now.hour <= 22

def control_shelly_device(device_id, action):
    print(f"Controlling device {device_id} with action {action}")
    print(f"URL: {SHELLY_URL}/relay/{device_id}?turn={action}")


def check_temperature_limits():
    
    config = get_configuration()
    
    subscribers = get_subscribers()
    

    for mac, config_data in config.items():
        
        # Get the latest temperature measurement for the current name
        latest_measurement = get_latest_measurement(config_data['name'])

        if latest_measurement:
            calibrated_temperature = float(latest_measurement['temperature_calibrated'])
            high_limit = float(config_data['alarms']['high']) if config_data['alarms']['high'] is not None else None
            low_limit = float(config_data['alarms']['low']) if config_data['alarms']['low'] is not None else None
            critical_low_limit = float(config_data['alarms']['critical_low']) if config_data['alarms']['critical_low'] is not None else None
            critical_high_limit = float(config_data['alarms']['critical_high']) if config_data['alarms']['critical_high'] is not None else None
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
            
            for deviceAction in config_data['deviceActions']:
                on_low = float(deviceAction['on_low']) if deviceAction['on_low'] is not None else None
                off_low = float(deviceAction['off_low']) if deviceAction['off_low'] is not None else None
                on_high = float(deviceAction['on_high']) if deviceAction['on_high'] is not None else None
                off_high = float(deviceAction['off_high']) if deviceAction['off_high'] is not None else None
                device_id = deviceAction['device_id']

                if on_low is not None and calibrated_temperature < on_low:
                    control_shelly_device(device_id, 'on')
                if off_low is not None and calibrated_temperature > off_low:
                    control_shelly_device(device_id, 'off')
                if on_high is not None and calibrated_temperature > on_high:
                    control_shelly_device(device_id, 'on')
                if off_high is not None and calibrated_temperature < off_high:
                    control_shelly_device(device_id, 'off')
    set_last24h_min_max()


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


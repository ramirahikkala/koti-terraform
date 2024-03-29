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
shelly_devices_table = dynamodb.Table('shelly_devices')
   

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

def get_today_measurement(name):
    response = stats_table.get_item(
        Key={"measurement_name": name, "statistics_type": "today"}
    )

    if "Item" in response:
        stats_item = response["Item"]
        return {
            "min": stats_item["temperature"]["min"]["value"],
            "min_datetime": stats_item["temperature"]["min"]["datetime"],
            "max": stats_item["temperature"]["max"]["value"],
            "max_datetime": stats_item["temperature"]["max"]["datetime"],
            "latest": {
                "datetime": datetime.strptime(
                    stats_item["temperature"]["latest"]["datetime"],
                    "%Y-%m-%dT%H:%M:%S.%fZ"),
                "datetime_str": stats_item["temperature"]["latest"]["datetime"],
                "temperature": stats_item["temperature"]["latest"]["value"],
                "temperature_calibrated": stats_item["temperature"]["latest"]["value"]                
            }
        }

    return {
        "min": -99,
        "min_datetime": datetime.now(),
        "max": 99,
        "max_datetime": datetime.now(),
        "latest": None
    }


def is_daytime():
    now = datetime.now()
    return now.hour >= 8 and now.hour <= 22

def update_shelly_state(device_id, state):

    
    # Update the device status in the shelly_devices table
    response = shelly_devices_table.update_item(
        Key={
            'id': device_id,
        },
        UpdateExpression="set deviceStatus=:s, lastUpdated=:lu",
        ExpressionAttributeValues={
            ':s': state,
            ':lu': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        },
        ReturnValues="UPDATED_NEW"
    )

    # Return the response for confirmation
    return response

def do_action(device_id, action):

    # TODO: This leads to Request limit reached error:
    # shelly_status = fetch_shelly_device_status(device_id)
    # if not shelly_status['online']:
    #     print(f"Device {device_id} is offline")
    #     send_telegram_message(f"Device {device_id} is offline")
    #     return

    print(f"Controlling device {device_id} with action {action}")
    data = {
        'channel': '0',
        'turn': action,
        'id': device_id,
        'auth_key': SHELLY_AUTH
    }

    # Send the request to the Shelly device
    response = requests.post(f"{SHELLY_URL}/device/relay/control", data=data)
    
    if response.status_code != 200:
        print(f"Error controlling device {device_id}: {response.status_code}: {response.text}")
        send_telegram_message(f"Error controlling device {device_id}: {response.status_code}: {response.text}")
    else:
        update_shelly_state(device_id, action)


def fetch_shelly_device_status(device_id):
    data = {
        'id': device_id,
        'auth_key': SHELLY_AUTH
    }
    response = requests.post(f"{SHELLY_URL}/device/status", data=data)
    if response.status_code == 200:
        device_info = response.json()
        if device_info.get('isok'):
            return device_info.get('data')
        else:
            print(f"Unable to fetch the status of device {device_id}")
    else:
        print(f"Failed to get status for device {device_id}. Status code: {response.status_code}")
    return None



def control_shelly_device(device_id, action):

    # Get the current device status from the DynamoDB table
    response = shelly_devices_table.get_item(
        Key={
            'id': device_id,
        }
    )

    # If the item was found in the table
    if 'Item' in response:
        current_status = response['Item'].get('deviceStatus')
        last_updated_str = response['Item'].get('lastUpdated')

        # Parse the lastUpdated string into a datetime object
        last_updated = datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%S.%fZ')

        # If the current status is different from the intended action or if the last status update was more than one hour ago
        if current_status != action or datetime.utcnow() - last_updated > timedelta(hours=1):
            do_action(device_id, action)
            
    else:
        # If the device was not found in the table, just do the action (this is for new devices)
        do_action(device_id, action)

def get_all_shelly_devices():
    shelly_devices_table = dynamodb.Table('shelly_devices')
    response = shelly_devices_table.scan()
    shelly_devices = response['Items']
    return shelly_devices


def check_temperature_limits():
    
    config = get_configuration()
    

    # Implement this later. Should check the status somehow time to time
    # shelly_devices = get_all_shelly_devices()

    # for db_device in shelly_devices:

    #     shelly_device_status = fetch_shelly_device_status(db_device['id'])
    #     if shelly_device_status != db_device['deviceStatus']:            
    #         print(f"Device in DynamoDB is out of sync with the actual device status. Updating DynamoDB...")
    #         update_shelly_state(db_device['id'], shelly_device_status)
    #         # Warn user
    #         send_telegram_message(f"Device {db_device['id']} is out of sync with the actual device status. Updating DynamoDB...")
    

    for mac, config_data in config.items():
        
        # Get the latest temperature measurement for the current name        
        today = get_today_measurement(config_data['name'])
        latest_measurement = today['latest']

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
                send_telegram_message(message)
            
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


def send_telegram_message(text):
    
    subscribers = get_subscribers()
    
    for chat_id in subscribers:

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


import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
import traceback
import datetime
import decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(CustomJSONEncoder, self).default(obj)


def get_configuration():
    dynamodb = boto3.resource('dynamodb')
    config_table = dynamodb.Table('ruuvi_configuration')
    response = config_table.scan()
    data = response['Items']
    config = {}
    for item in data:
        name = item['name']
        config[name] = {
            'name': item['name'],
            'mac': item['mac'],
            'temperatureOffset': item.get('temperatureOffset', 0),
            'temperatureMonitoring_high': item.get('temperatureMonitoring_high', None),
            'temperatureMonitoring_low': item.get('temperatureMonitoring_low', None)
        }
    return config


def get_latest_measurement(name):
    response = table.query(
        KeyConditionExpression=Key('name').eq(name),
        ScanIndexForward=False,  # Sort by datetime in descending order
        Limit=1
    )
    if(response['Items']):
        item = response['Items'][0]
        dt = datetime.datetime.strptime(item['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        item['datetime'] = dt
        item['datetime_str'] = item['datetime']
        return item
    return None

def get_min_max_measurement(name, latest_measurement):
    if latest_measurement is None:
        return {'min': None, 'max': None}

    latest_time_str = latest_measurement['datetime'].strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # Calculate the time 24 hours before the latest measurement
    start_time = latest_measurement['datetime'] - timedelta(days=1)
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # Query the measurements of the last 24 hours
    response = table.query(
        KeyConditionExpression=Key('name').eq(name) & Key('datetime').between(start_time_str, latest_time_str),
        ScanIndexForward=False  # Sort by datetime in descending order
    )

    min_temp = float('inf')
    min_datetime = None
    max_temp = float('-inf')
    max_datetime = None

    for item in response['Items']:
        temp = float(item['temperature_calibrated'])
        if temp < min_temp:
            min_temp = temp
            min_datetime = item['datetime']
        if temp > max_temp:
            max_temp = temp
            max_datetime = item['datetime']

    return {
        'min': min_temp if min_datetime else None,
        'min_datetime': min_datetime,
        'max': max_temp if max_datetime else None,
        'max_datetime': max_datetime
    }

def get_latest_and_min_max_temperatures():
    config = get_configuration()
    latest_and_min_max_temps = {}
    for name, data in config.items():
        latest_measurement = get_latest_measurement(name)
        min_max_measurement = get_min_max_measurement(name, latest_measurement)
        latest_and_min_max_temps[name] = {
            "latest": latest_measurement,
            "min_max": min_max_measurement
        }
    return latest_and_min_max_temps


def lambda_handler(event, context):
    try:
        latest_and_min_max_temps = get_latest_and_min_max_temperatures()
        response_dict = {}
        response_dict["temperatures"] = {}

        for name, data in latest_and_min_max_temps.items():            
            temp_latest = data['latest']
            temp_min_max = data['min_max']
            response_dict["temperatures"][name] = {
                "latest": temp_latest,
                "min_max": temp_min_max
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': 'https://temperature-visualizer.vercel.app',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps(response_dict, cls=CustomJSONEncoder)
        }
    except Exception as e:
        print("Exception occurred:")
        print(str(e))
        print(traceback.format_exc())  # Print the complete traceback information
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"result": "Error getting latest temperatures"})
        }

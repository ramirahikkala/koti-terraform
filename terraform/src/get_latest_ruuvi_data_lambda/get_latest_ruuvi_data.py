import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
import traceback
import datetime
import decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')
stats_table = dynamodb.Table('measurement_stats')


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if obj.tzinfo is None:
                # The datetime object is naive. Assume UTC.
                return obj.replace(tzinfo=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            else:
                # The datetime object is timezone-aware.
                return obj.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
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
        Limit=1,
        
    )
    if(response['Items']):
        item = response['Items'][0]
        dt = datetime.datetime.strptime(item['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        item['datetime'] = dt
        item['datetime_str'] = item['datetime']
        return item
    return None

def get_min_max_measurement(name, latest_measurement):
    response = stats_table.query(
        KeyConditionExpression=Key('measurement_name').eq(name)
        & Key('statistics_type').eq('past24h'),
        Limit=1,
    )

    stats_item = response['Items'][0]


    return {
        'min': stats_item['temperature']['min']['value'] ,
        'min_datetime': stats_item['temperature']['min']['datetime'],
        'max': stats_item['temperature']['max']['value'],
        'max_datetime': stats_item['temperature']['max']['datetime']
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

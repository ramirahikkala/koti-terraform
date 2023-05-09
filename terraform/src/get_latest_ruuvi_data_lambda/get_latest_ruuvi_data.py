import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import traceback

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')


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


def get_latest_measurement(name, config):
    response = table.query(
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


def get_latest_temperatures():
    config = get_configuration()
    latest_temps = {}
    for name, data in config.items():
        measurement = get_latest_measurement(name, config)
        if measurement is not None:
            latest_temps[data["name"]] = measurement
    return latest_temps


def lambda_handler(event, context):
    try:
        latest_temps = get_latest_temperatures()
        response_dict = {}
        response_dict["temperatures"] = {}
        response_dict["temperatures"]["latest"] = {}
        
        for name, data in latest_temps.items():
            temp = data['temperature_calibrated']
            response_dict["temperatures"]["latest"][name] = temp

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': 'https://temperature-visualizer.vercel.app',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
            "body": json.dumps(response_dict)
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

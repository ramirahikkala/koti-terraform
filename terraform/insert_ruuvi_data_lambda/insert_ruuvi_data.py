import json
import boto3
from datetime import datetime
import traceback

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')
config_table = dynamodb.Table('ruuvi_configuration')

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
            'lastAlarmState': item.get('lastAlarmState', None),
        }
    return config


def lambda_handler(event, context):
    try:
        config = get_configuration()
        body = json.loads(event['body'])
        mac = body['name']
        config_for_mac = config[mac]
        name = config_for_mac['name'] 
        temperature = body['temperature']
        temperature_calibrated =format(float(body['temperature']) + float(config_for_mac['temperatureOffset']), '.2f')
        humidity = body['humidity']
        pressure = body['pressure']

        # Use the current datetime as the sort key.
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Store the data in DynamoDB.
        response = table.put_item(
            Item={
                'name': name,
                'mac': mac,
                'datetime': now,
                'temperature': temperature,
                'temperature_calibrated': temperature_calibrated,
                'humidity': humidity,
                'pressure': pressure
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Data inserted successfully'})
        }
    except Exception as e:
        print("Exception occurred:")
        print(str(e))
        print(traceback.format_exc())  # Print the complete traceback information
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Error inserting data'})
        }

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
        }
    return config

def get_configuration_for_new_sensor(mac):
    return {
        'mac': mac,
        'name': 'name_for_' + mac,
        'type': 'ruuvitag',
        'temperatureOffset': '0.0',
        'alarms': {
            'critical_high': 35,
            'high': 30,
            'critical_low': 3,
            'low': 5,
        },
        'lastAlarmState': None,
        'deviceActions': [
            {
                'device_id': 'cooling_device_id',
                'off_high': 35,
                'on_high': 36
            },
            {
                'device_id': 'heating_device_id',
                'off_low': 11,
                'on_low': 10
            }
        ]
    }



def lambda_handler(event, context):
    try:
        config = get_configuration()
        body = json.loads(event['body'])
        mac = body['name']
        if mac not in config:
            new_config = get_configuration_for_new_sensor(mac)
            config[mac] = new_config
            response = config_table.put_item(
                Item=new_config
            )
        config_for_mac = config[mac]
        name = config_for_mac['name']
        temperature = body['temperature']
        temperature_calibrated = format(float(body['temperature']) + float(config_for_mac['temperatureOffset']), '.2f')
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


import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        name = body['name']
        temperature = body['temperature']
        temperature_calibrated = body['temperature_calibrated']
        humidity = body['humidity']
        pressure = body['pressure']

        # Use the current datetime as the sort key.
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Store the data in DynamoDB.
        response = table.put_item(
            Item={
                'name': name,
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
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Error inserting data'})
        }

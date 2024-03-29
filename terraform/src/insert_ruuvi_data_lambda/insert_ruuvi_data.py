import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime, timedelta

import traceback

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi')
config_table = dynamodb.Table('ruuvi_configuration')
stats_table = dynamodb.Table('measurement_stats')


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

def clear_item(stats_item, temperature, measurement_time, name, stats_type):
    stats_item = {
        'measurement_name': name,
        'statistics_type': stats_type,
        'temperature': {                
            'min': { 'value': temperature, 'datetime': measurement_time },
            'max': { 'value': temperature, 'datetime': measurement_time },
            'latest': { 'value': temperature, 'datetime': measurement_time },
            'sum': temperature,
            'count': 1,
        },
    }
    return stats_item

def set_temperature_stats(name, temperature, measurement_time):

    set_stats_for_type(name, temperature, measurement_time, 'alltime')
    set_stats_for_type(name, temperature, measurement_time, 'today')

def set_stats_for_type(name, temperature, measurement_time, stats_type):

    # Get the current daily min/max values for this sensor.
    response = stats_table.get_item(
        Key={"measurement_name": name, "statistics_type": "today"}
    )   
    
    temperature = Decimal(str(temperature))    

    if 'Item' not in response:
        stats_item = clear_item(stats_item, temperature, measurement_time, name, stats_type)
    else:
        # Otherwise, update the min/max values with the current measurement.
        stats_item = response['Item']

        date_string = stats_item['temperature']['latest']['datetime']
        latest_measurement_date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").date()

        # Get the current date
        current_date = datetime.now().date()

        #Turn of the day. Store yesterdays values and clear todays
        if stats_type == 'today' and latest_measurement_date == current_date - timedelta(days=1):
            stats_item['statistics_type'] = 'yesterday'
            stats_table.put_item(Item=stats_item)

            stats_item = clear_item(stats_item, temperature, measurement_time, name, stats_type)            
            
             
        if stats_item['temperature']['min']['value'] > temperature:
            stats_item['temperature']['min'] = { 'value': temperature, 'datetime': measurement_time }
            
        if stats_item['temperature']['max']['value'] < temperature:
            stats_item['temperature']['max'] = { 'value': temperature, 'datetime': measurement_time }
            
        stats_item['temperature']['sum'] += Decimal(str(temperature))
        stats_item['temperature']['count'] += Decimal('1')    
        stats_item['temperature']['latest'] = { 'value': temperature, 'datetime': measurement_time }

    

    # Store the updated statistics data in DynamoDB.
    response = stats_table.put_item(Item=stats_item)



def lambda_handler(event, context):
    try:
        config = get_configuration()
        body = json.loads(event['body'])
        mac = body.get('name', '')
        if mac not in config:
            new_config = get_configuration_for_new_sensor(mac)
            config[mac] = new_config
            response = config_table.put_item(
                Item=new_config
            )
        config_for_mac = config[mac]
        name = config_for_mac['name']
        temperature_raw = body.get('temperature', 0)
        temperature_calibrated = format(float(body.get('temperature', 0)) + float(config_for_mac['temperatureOffset']), '.2f')
        humidity = body.get('humidity', 0)
        pressure = body.get('pressure', 0)
        battery = body.get('battery', 0)
        data_format = body.get('data_format', 0)
        measurement_sequence_number = body.get('measurement_sequence_number', 0)
        acceleration_z = body.get('acceleration_z', 0)
        acceleration = body.get('acceleration', 0)
        acceleration_y = body.get('acceleration_y', 0)
        acceleration_x = body.get('acceleration_x', 0)
        tx_power = body.get('tx_power', 0)
        movement_counter = body.get('movement_counter', 0)
        rssi = body.get('rssi', 0)

        # Use the current datetime as the sort key.
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Store the data in DynamoDB.
        response = table.put_item(
            Item={
                'name': name,
                'mac': mac,
                'datetime': now,
                'temperature_raw': temperature_raw,
                'temperature': temperature_calibrated,
                'temperature_calibrated': temperature_calibrated,
                'humidity': humidity,
                'pressure': pressure,
                'battery': battery,
                'data_format': data_format,
                'measurement_sequence_number': measurement_sequence_number,
                'acceleration_z': acceleration_z,
                'acceleration': acceleration,
                'acceleration_y': acceleration_y,
                'acceleration_x': acceleration_x,
                'tx_power': tx_power,
                'movement_counter': movement_counter,
                'rssi': rssi
            }
        )
        
        set_temperature_stats(name, temperature_calibrated, now)

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




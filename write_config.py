import boto3

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ruuvi_configuration')

# Your existing configuration data
config_data = {
    "ruuvitags":
    [
        {
            "name": "Alakerta",
            "MAC": "F2:9F:28:C0:09:3E",
            "temperatureOffset": "0.68"
        },
        {
            "name": "Ulko",
            "MAC": "F7:66:27:26:96:39",
            "temperatureOffset": "0"
        },
        {
            "name": "Yläkerta",
            "MAC": "C3:E8:BC:6E:13:8D",
            "temperatureOffset": "0.98"
        },
        {
            "name": "Kasvihuone",
            "MAC": "F3:04:39:3B:DC:2D",
            "temperatureOffset": "0.00"
        }
    ],
    "temperatureMonitoring":
    [
        {
            "name": "Alakerta",
            "high": 25,
            "low": 21
        },
        {
            "name": "Yläkerta",
            "high": 25,
            "low": 19
        },
        {
            "name": "Kasvihuone",
            "high": 28,
            "low": 5
        }

    ]
}

# Insert ruuvitags into DynamoDB
for tag in config_data["ruuvitags"]:
    table.put_item(Item={
        'mac': tag["MAC"],
        'name': tag["name"],
        'type': 'ruuvitag',
        'temperatureOffset': tag["temperatureOffset"]
    })

# Insert temperatureMonitoring data into DynamoDB
for monitor in config_data["temperatureMonitoring"]:
    # Find the corresponding MAC address for the name
    mac = next((tag["MAC"] for tag in config_data["ruuvitags"] if tag["name"] == monitor["name"]), None)
    if mac:
        table.update_item(
            Key={'mac': mac},
            UpdateExpression="SET #type_high = :high, #type_low = :low",
            ExpressionAttributeNames={
                "#type_high": "temperatureMonitoring_high",
                "#type_low": "temperatureMonitoring_low"
            },
            ExpressionAttributeValues={
                ":high": monitor["high"],
                ":low": monitor["low"]
            }
        )

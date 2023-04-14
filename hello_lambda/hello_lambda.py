def handler(event, context):
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": "{\"message\": \"Hello from Lambda!\"}"
    }
    return response
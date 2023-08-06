import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
import traceback
import datetime
import decimal

dynamodb = boto3.resource("dynamodb")
ruuvi_data_table = dynamodb.Table("ruuvi")
stats_table = dynamodb.Table("measurement_stats")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if obj.tzinfo is None:
                # The datetime object is naive. Assume UTC.
                return (
                    obj.replace(tzinfo=datetime.timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            else:
                # The datetime object is timezone-aware.
                return (
                    obj.astimezone(datetime.timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(CustomJSONEncoder, self).default(obj)


def get_configuration():
    dynamodb = boto3.resource("dynamodb")
    config_table = dynamodb.Table("ruuvi_configuration")
    response = config_table.scan()
    data = response["Items"]
    config = {}
    for item in data:
        name = item["name"]
        config[name] = {
            "name": item["name"],
            "mac": item["mac"],
            "temperatureOffset": item.get("temperatureOffset", 0),
            "temperatureMonitoring_high": item.get("temperatureMonitoring_high", None),
            "temperatureMonitoring_low": item.get("temperatureMonitoring_low", None),
        }
    return config


def get_latest_measurement(name):
    response = ruuvi_data_table.query(
        KeyConditionExpression=Key("name").eq(name),
        ScanIndexForward=False,  # Sort by datetime in descending order
        Limit=1,
    )
    if response["Items"]:
        item = response["Items"][0]
        dt = datetime.datetime.strptime(item["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ")
        item["datetime"] = dt
        item["datetime_str"] = item["datetime"]
        return item
    return None


def get_today_measurement(name):
    response = stats_table.get_item(
        Key={"measurement_name": name, "statistics_type": "today"}
    )

    if "Item" in response:
        stats_item = response["Item"]
        print(name)
        return {
            "min": stats_item["temperature"]["min"]["value"],
            "min_datetime": stats_item["temperature"]["min"]["datetime"],
            "max": stats_item["temperature"]["max"]["value"],
            "max_datetime": stats_item["temperature"]["max"]["datetime"],
            "latest": {
                "datetime": datetime.datetime.strptime(
                    stats_item["temperature"]["latest"]["datetime"],
                    "%Y-%m-%dT%H:%M:%S.%fZ"),
                "datetime_str": stats_item["temperature"]["latest"]["datetime"],
                "temperature": stats_item["temperature"]["latest"]["value"],
                "temperature_calibrated": stats_item["temperature"]["latest"]["value"]                
            }
        }

    return {
        "min": -99,
        "min_datetime": datetime.datetime.now(),
        "max": 99,
        "max_datetime": datetime.datetime.now(),
        "latest": None
    }


def get_latest_and_min_max_temperatures():
    config = get_configuration()
    latest_and_min_max_temps = {}
    for name, data in config.items():
        today = get_today_measurement(name)
        latest_measurement = today['latest']
        min_max_measurement = today
        latest_and_min_max_temps[name] = {
            "latest": latest_measurement,
            "min_max": min_max_measurement,
        }
    return latest_and_min_max_temps


def get_specific_and_min_max_temperatures(measurement_point, time_range):
    response = ruuvi_data_table.query(
        KeyConditionExpression=Key("name").eq(measurement_point)
        & Key("datetime").gte(
            str(datetime.datetime.utcnow() - timedelta(hours=time_range))
        ),
    )
    return response["Items"]


def get_return_data(body, status_code=200):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",  #'https://temperature-visualizer.vercel.app',
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(body, cls=CustomJSONEncoder),
    }


def lambda_handler(event, context):
    try:
        if (
            "queryStringParameters" in event
            and event["queryStringParameters"] is not None
        ):
            query_params = event["queryStringParameters"]
            if "measurementPoint" in query_params and "timeRange" in query_params:
                measurement_point = query_params["measurementPoint"]
                time_range = int(
                    query_params["timeRange"]
                )  # timeRange is an integer representing hours
                response_dict = get_specific_and_min_max_temperatures(
                    measurement_point, time_range
                )
                return get_return_data(response_dict)

        # if we reach this point, either there were no query parameters or they were incomplete
        latest_and_min_max_temps = get_latest_and_min_max_temperatures()

        response_dict = {}
        response_dict["temperatures"] = {}

        for name, data in latest_and_min_max_temps.items():
            temp_latest = data["latest"]
            temp_min_max = data["min_max"]
            response_dict["temperatures"][name] = {
                "latest": temp_latest,
                "min_max": temp_min_max,
            }

        response_dict["config"] = get_configuration()

        return get_return_data(response_dict)

    except Exception as e:
        print("Exception occurred:")
        print(str(e))
        print(traceback.format_exc())  # Print the complete traceback information
        return get_return_data({"result": "Error getting latest temperatures"}, 400)

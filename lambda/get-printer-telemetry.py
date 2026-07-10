import os
import json
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME", "PrinterTelemetry"))


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    device_id = params.get("deviceId", "printer-001")
    limit = int(params.get("limit", "50"))

    resp = table.query(
        KeyConditionExpression=Key("deviceId").eq(device_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    items = resp.get("Items", [])

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(items, default=_json_default),
    }


def _json_default(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError

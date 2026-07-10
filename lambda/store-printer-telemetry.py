import os
from decimal import Decimal
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME", "PrinterTelemetry"))

sns = boto3.client("sns")
ALERT_TOPIC_ARN = os.environ.get("ALERT_TOPIC_ARN", "")

NOZZLE_MAX_C = 235.0
VIBRATION_MAX = 0.4


def lambda_handler(event, context):
    device_id = event["deviceId"]
    timestamp = event["timestamp"]
    nozzle = float(event["nozzleTempC"])
    bed = float(event["bedTempC"])
    vibration = float(event["vibration"])

    reasons = []
    if nozzle > NOZZLE_MAX_C:
        reasons.append(f"nozzle {nozzle}C > {NOZZLE_MAX_C}C")
    if vibration > VIBRATION_MAX:
        reasons.append(f"vibration {vibration} > {VIBRATION_MAX}")

    is_anomaly = len(reasons) > 0
    reason = "; ".join(reasons) if is_anomaly else "ok"

    item = {
        "deviceId": device_id,
        "timestamp": timestamp,
        "nozzleTempC": Decimal(str(nozzle)),
        "bedTempC": Decimal(str(bed)),
        "vibration": Decimal(str(vibration)),
        "status": event.get("status", "unknown"),
        "isAnomaly": is_anomaly,
        "reason": reason,
    }
    table.put_item(Item=item)

    if is_anomaly:
        print(f"ANOMALY {device_id} @ {timestamp}: {reason}")
        _send_alert(device_id, timestamp, reason, nozzle, vibration)

    return {"stored": True, "isAnomaly": is_anomaly}


def _send_alert(device_id, timestamp, reason, nozzle, vibration):
    if not ALERT_TOPIC_ARN:
        print("ALERT_TOPIC_ARN not set; skipping SNS publish")
        return
    try:
        sns.publish(
            TopicArn=ALERT_TOPIC_ARN,
            Subject=f"Printer anomaly: {device_id}"[:100],
            Message=(
                f"Anomaly detected on {device_id}\n"
                f"Time: {timestamp}\n"
                f"Reason: {reason}\n"
                f"Nozzle: {nozzle} C\n"
                f"Vibration: {vibration}"
            ),
        )
    except Exception as e:
        print(f"SNS publish failed: {e}")

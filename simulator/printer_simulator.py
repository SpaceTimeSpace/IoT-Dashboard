"""
Printer telemetry simulator -> AWS IoT Core (MQTT over mutual TLS).

Setup:
  1) pip install awsiotsdk
  2) Put your downloaded cert files in a local folder (NOT in git).
  3) Update ENDPOINT (IoT Core -> Settings -> Device data endpoint).
  4) Update CERT_PATH, KEY_PATH, CA_PATH to point at your cert files.
  5) Run:  python printer_simulator.py
  6) Watch messages in IoT Core MQTT test client (subscribe to printers/#).

Stop with Ctrl+C.
"""

import time
import json
import random
from datetime import datetime, timezone

from awscrt import mqtt
from awsiot import mqtt_connection_builder

# ---------- CONFIG (edit these) ----------
ENDPOINT = "YOUR-DEVICE-ENDPOINT-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "printer-001"
TOPIC = "printers/printer-001/telemetry"

CERT_PATH = "path/to/printer-001.certificate.pem.crt"
KEY_PATH = "path/to/printer-001.private.pem.key"
CA_PATH = "path/to/AmazonRootCA1.pem"

PUBLISH_INTERVAL_SECONDS = 3
ANOMALY_CHANCE = 0.10
# -----------------------------------------


def build_reading():
    nozzle_temp = round(random.gauss(205, 2), 1)
    bed_temp = round(random.gauss(60, 1), 1)
    vibration = round(abs(random.gauss(0.12, 0.03)), 3)
    status = "printing"

    if random.random() < ANOMALY_CHANCE:
        nozzle_temp = round(random.uniform(240, 270), 1)
        vibration = round(random.uniform(0.5, 1.0), 3)
        status = "warning"

    return {
        "deviceId": CLIENT_ID,
        "nozzleTempC": nozzle_temp,
        "bedTempC": bed_temp,
        "vibration": vibration,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=CERT_PATH,
        pri_key_filepath=KEY_PATH,
        ca_filepath=CA_PATH,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30,
    )

    print(f"Connecting to {ENDPOINT} as '{CLIENT_ID}' ...")
    connection.connect().result()
    print("Connected. Publishing telemetry (Ctrl+C to stop).\n")

    try:
        while True:
            reading = build_reading()
            connection.publish(
                topic=TOPIC,
                payload=json.dumps(reading),
                qos=mqtt.QoS.AT_LEAST_ONCE,
            )
            flag = "  <-- ANOMALY" if reading["status"] == "warning" else ""
            print(f"Published: {reading}{flag}")
            time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        connection.disconnect().result()
        print("Disconnected.")


if __name__ == "__main__":
    main()

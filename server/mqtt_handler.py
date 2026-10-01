import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv
import time

from device_manager import update_device, show_devices
from priority_manager import add_message
from database import get_device_priority, create_priority_request
from monitor import message_received, message_rejected, priority_message


BROKER = "localhost"
PORT = 1883
TOPIC = "devices/+/data"

load_dotenv()

USERNAME = "SERVER"
PASSWORD = os.getenv("MQTT_SERVER_PASSWORD")


def validate_data(data):
    required_fields = ["device_id", "sensor", "value", "unit", "priority"]

    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"

    if not isinstance(data["device_id"],str):
        return False, f"device_id must be a string"

    if not isinstance(data["sensor"],str):
        return False, f"sensor must be a string"

    if not isinstance(data["unit"],str):
        return False, f"unit must be a string"

    if not isinstance(data["priority"],str):
        return False, f"priority must be a string"

    if not isinstance(data["value"], (int,float)):
        return False, f"value must be a number"


    if data["priority"] not in ["normal", "high"]:
        return False, "invalid property"


    return True, "valid"
    

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker!")

    client.subscribe(TOPIC)

    print(f"Subscribed to: {TOPIC}")


_priority_cache = {}
CACHE_TTL = 30

def get_device_priority_cached(device_id):
    now = time.monotonic()
    entry = _priority_cache.get(device_id)
    if entry and now - entry[1] < CACHE_TTL:
        return entry[0]
    priority = get_device_priority(device_id)
    _priority_cache[device_id] = (priority, now)
    return priority


_last_escalation = {}
ESCALATION_COOLDOWN = 10

def on_message(client, userdata, message):
    message_received()

    payload = (message.payload.decode())

    try:
        data = json.loads(payload)

    except json.JSONDecodeError:
        print("Rejected: Invalid JSON")
        message_rejected()
        return

    if not isinstance(data, dict):
        print("Rejected: JSON must contain an object")
        return

    valid, reason = validate_data(data)

    if not valid:
        print(f"Rejected: {reason}")
        return

    topic_device_id = message.topic.split("/")[1]

    if data["device_id"] != topic_device_id:
        print("Rejected: Device ID does not match topic")
        return

    print("\nAccepted Data")
    # print(f"Device: {data['device_id']}")
    # print(f"Sensor: {data['sensor']}")
    # print(f"Value: {data['value']} {data['unit']}")

    device_priority = get_device_priority_cached(data['device_id'])

    if device_priority is None:
        print("Rejected: Device is not registered")
        message_rejected()
        return

    if device_priority == "high" or data['priority'] == "normal":
        data['priority'] = device_priority
        add_message(data)
        priority_message(device_priority)
        return

    reason = data.get("reason")
    if not isinstance(reason, str) or reason.strip() == "":
        print("Rejected: A non-empty text reason is required for priority escalation")
        message_rejected()
        return

    now = time.monotonic()
    last = _last_escalation.get(data['device_id'])
    if last is not None and now - last < ESCALATION_COOLDOWN:
        print(f"Rejected: {data['device_id']} escalation requested too soon")
        message_rejected()
        return
    _last_escalation[data['device_id']] = now

    request_id = create_priority_request(data['device_id'], data['priority'], reason, data)
    print(f"Priority escalation requires approval | Request ID : {request_id}")


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.username_pw_set(USERNAME, PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT broker...")

    client.connect(BROKER, PORT)

    client.loop_forever()
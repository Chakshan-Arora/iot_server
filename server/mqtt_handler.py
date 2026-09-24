import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv

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


    # if data["priority"] not in ["normal", "high"]:
    #     return False, "invalid property"


    return True, "valid"
    

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker!")

    client.subscribe(TOPIC)

    print(f"Subscribed to: {TOPIC}")


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
    print(f"Device: {data['device_id']}")
    print(f"Sensor: {data['sensor']}")
    print(f"Value: {data['value']} {data['unit']}")

    device_priority = get_device_priority(data['device_id'])
    if device_priority is None:
        print("Rejected: Device is not registered")
        message_rejected()
        return

    elif device_priority == "high":
        add_message(data)

    else:
        if data['priority'] == "normal":
            add_message(data)


        else:
            if "reason" not in data:
                print("Rejected: Reason required for priority escalation")
                message_rejected()
                return
            if not isinstance(data['reason'],str):
                print("Rejected: Reason must be a string")
                message_rejected()
                return
            if data['reason'].strip() == "":
                print("Rejected: Reason cant be empty")
                message_rejected()
                return

            request_id = create_priority_request(data['device_id'], data['priority'], data['reason'], data)

            print(f"Priority escalation requires approval | Request ID : {request_id}")


    data['priority'] = device_priority
    print(f"Priority: {data['priority']}")

    print()
    priority_message(data["priority"])
    # update_device(data['device_id'])
    # show_devices()


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.username_pw_set(USERNAME, PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT broker...")

    client.connect(BROKER, PORT)

    client.loop_forever()
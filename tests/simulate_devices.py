import json
import random
import time
import threading
import os
from dotenv import load_dotenv

import paho.mqtt.client as mqtt


BROKER = "localhost"
PORT = 1883

MESSAGES_PER_DEVICE = 100
SEND_DELAY = 0.1

load_dotenv()

DEVICES = [
    {
        "device_id": device_id,
        "password": os.getenv(f"{device_id}_PASSWORD"),
        "sensor": sensor,
        "priority": priority,
    }
    for device_id, sensor, priority in [
        ("ESP32_01", "ultrasonic", "high"),
        ("ESP32_02", "light", "normal"),
        ("ESP32_03", "accelerometer", "normal"),
        ("ESP32_04", "touch", "high"),
        ("ESP32_05", "light", "normal"),
        ("ESP32_06", "ultrasonic", "normal"),
        ("ESP32_07", "accelerometer", "normal"),
        ("ESP32_08", "light", "high"),
        ("ESP32_09", "touch", "normal"),
        ("ESP32_10", "ultrasonic", "normal"),
    ]
]

escalations_sent = []


def generate_value(sensor):
    if sensor == "ultrasonic":
        return random.randint(10, 200)
    elif sensor == "light":
        return random.randint(0, 100)
    elif sensor == "accelerometer":
        return round(random.uniform(0.8, 1.2), 2)
    elif sensor == "touch":
        return random.randint(0, 1)
    return 0


def get_unit(sensor):
    if sensor == "ultrasonic":
        return "cm"
    elif sensor == "light":
        return "percent"
    elif sensor == "accelerometer":
        return "g"
    elif sensor == "touch":
        return "boolean"
    return "unknown"


def simulate_device(device):

    device_id = device["device_id"]
    sensor = device["sensor"]
    priority = device["priority"]

    escalate_at = None
    if priority == "normal":
        escalate_at = random.randint(10, MESSAGES_PER_DEVICE - 10)

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=device_id
    )

    client.username_pw_set(device_id, device["password"])

    connected = threading.Event()

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"{device_id} refused: {reason_code}")
        else:
            connected.set()

    client.on_connect = on_connect

    try:
        client.connect(BROKER, PORT)
        client.loop_start()

        if not connected.wait(5):
            print(f"{device_id} could not connect")
            client.loop_stop()
            return

        print(f"{device_id} connected")

        topic = f"devices/{device_id}/data"

        for i in range(MESSAGES_PER_DEVICE):

            value = generate_value(sensor)
            unit = get_unit(sensor)

            data = {
                "device_id": device_id,
                "sensor": sensor,
                "value": value,
                "unit": unit,
                "priority": priority
            }
            label = priority

            if i == escalate_at:
                data["priority"] = "high"
                data["reason"] = f"{device_id} detected an abnormal {sensor} reading"
                label = "HIGH (needs approval)"
                escalations_sent.append(device_id)

            client.publish(topic, json.dumps(data))

            print(f"{device_id} → {sensor}: {value} {unit} | Priority: {label}")

            time.sleep(SEND_DELAY)

        client.loop_stop()
        client.disconnect()

        print(f"{device_id} finished")

    except Exception as e:
        print(f"{device_id} error: {e}")


def main():

    threads = []

    print("\nStarting device simulation...\n")

    for device in DEVICES:
        thread = threading.Thread(target=simulate_device, args=(device,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("\nAll simulated devices finished.")
    print(f"Escalation requests sent: {len(escalations_sent)} {sorted(escalations_sent)}")


if __name__ == "__main__":
    main()
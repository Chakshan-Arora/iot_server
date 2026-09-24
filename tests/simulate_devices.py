import json
import random
import time
import threading
import os
from dotenv import load_dotenv

import paho.mqtt.client as mqtt


BROKER = "localhost"
PORT = 1883

load_dotenv()

DEVICES = [
    {
        "device_id": "ESP32_01",
        "password": os.getenv("ESP32_01_PASSWORD"),
        "sensor": "ultrasonic",
        "priority": "high"
    },
    {
        "device_id": "ESP32_02",
        "password": os.getenv("ESP32_02_PASSWORD"),
        "sensor": "light",
        "priority": "normal"
    },
    {
        "device_id": "ESP32_03",
        "password": os.getenv("ESP32_03_PASSWORD"),
        "sensor": "accelerometer",
        "priority": "normal"
    },
    {
        "device_id": "ESP32_04",
        "password": os.getenv("ESP32_04_PASSWORD"),
        "sensor": "touch",
        "priority": "high"
    },
    {
        "device_id": "ESP32_05",
        "password": os.getenv("ESP32_05_PASSWORD"),
        "sensor": "light",
        "priority": "normal"
    },
    {
        "device_id": "ESP32_06",
        "password": os.getenv("ESP32_06_PASSWORD"),
        "sensor": "ultrasonic",
        "priority": "normal"
    },
    {
        "device_id": "ESP32_07",
        "password": os.getenv("ESP32_07_PASSWORD"),
        "sensor": "accelerometer",
        "priority": "normal"
    },
    {
        "device_id": "ESP32_08",
        "password": os.getenv("ESP32_08_PASSWORD"),
        "sensor": "light",
        "priority": "high"
    },
    {
        "device_id": "ESP32_09",
        "password": os.getenv("ESP32_09_PASSWORD"),
        "sensor": "touch",
        "priority": "normal"
    },
    {
        "device_id": "ESP32_10",
        "password": os.getenv("ESP32_10_PASSWORD"),
        "sensor": "ultrasonic",
        "priority": "normal"
    }
]


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

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=device_id
    )

    client.username_pw_set(
        device_id,
        device["password"]
    )

    try:
        client.connect(BROKER, PORT)

        print(f"{device_id} connected")

        client.loop_start()

        topic = f"devices/{device_id}/data"

        for i in range(10):

            value = generate_value(sensor)
            unit = get_unit(sensor)

            data = {
                "device_id": device_id,
                "sensor": sensor,
                "value": value,
                "unit": unit,
                "priority": priority
            }

            payload = json.dumps(data)

            client.publish(
                topic,
                payload
            )

            print(
                f"{device_id} → "
                f"{sensor}: {value} {unit} | "
                f"Priority: {priority}"
            )

            time.sleep(1)

        client.loop_stop()
        client.disconnect()

        print(f"{device_id} finished")

    except Exception as e:
        print(f"{device_id} error: {e}")


def main():

    threads = []

    print("\nStarting device simulation...\n")

    for device in DEVICES:

        thread = threading.Thread(
            target=simulate_device,
            args=(device,)
        )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("\nAll simulated devices finished.")


if __name__ == "__main__":
    main()


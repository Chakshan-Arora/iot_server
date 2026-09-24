from datetime import datetime
import time
import threading
from database import register_device, update_device_status, get_devices


devices = {}
OFFLINE_TIMEOUT = 60


def update_device(device_id):
    current_time = datetime.now()

    if device_id not in devices:
        devices[device_id] = {
            "status": "Online",
            "last_seen": current_time
        }

        print(f"Device {device_id} came online")

    else:
        devices[device_id]["status"] = "Online"
        devices[device_id]["last_seen"] = current_time


def check_offline_devices():
    while True:
        current_time = datetime.now()

        for device in get_devices():
            time_since_last_message = (current_time - device["last_seen"]).total_seconds()

            if time_since_last_message > OFFLINE_TIMEOUT:
                update_device_status(device['device_id'], device['status'])

    time.sleep(2)



def show_devices():
    print("\n--- Device Status ---")

    for device in get_devices():
        print(
            f"{device['device_id']} | "
            f"{device['status']} | "
            f"Last seen: {device['last_seen'].strftime('%Y-%m-%d %H:%M:%S')}"
        )

    print("---------------------\n")


def start_device_monitor():
    monitor_thread = threading.Thread(target=check_offline_devices, daemon=True)

    monitor_thread.start()


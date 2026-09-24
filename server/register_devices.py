from database import devices

device_list = [
    ("ESP32_01", "high"),
    ("ESP32_02", "normal"),
    ("ESP32_03", "normal"),
    ("ESP32_04", "high"),
    ("ESP32_05", "normal"),
    ("ESP32_06", "normal"),
    ("ESP32_07", "normal"),
    ("ESP32_08", "high"),
    ("ESP32_09", "normal"),
    ("ESP32_10", "normal")
]

for device_id, priority in device_list:

    devices.update_one(
        {"device_id": device_id},
        {
            "$set": {
                "priority": priority,
                "status": "Offline"
            }
        },
        upsert=True
    )

    print(f"Registered: {device_id} | Priority: {priority}")

print("\nAll 10 devices registered.")

from pymongo import MongoClient
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

database = client["MQTT"]

sensor_data = database["sensor_data"]

devices = database["devices"]

priority_requests = database["priority_requests"]


def save_sensor_data(data):
    document = {
        "device_id": data["device_id"],
        "sensor": data["sensor"],
        "value": data["value"],
        "unit": data["unit"],
        "priority": data["priority"],
        "timestamp": datetime.now()
    }

    sensor_data.insert_one(document)

    print("Data saved to MongoDB")


def register_device(device_id, sensor):

    current_time = datetime.now()

    devices.update_one(
        {"device_id": device_id},
        {
            "$set": {
                "status": "Online",
                "last_seen": current_time,
                "sensor": sensor
            }
        },
        upsert=True
    )

    print(f"Device registry updated: {device_id}")


def update_device_status(device_id, status):

    devices.update_one(
        {"device_id": device_id},
        {
            "$set": {
                "status": status,
                "last_seen": datetime.now()
            }
        }
    )

def get_devices():
    return devices.find()


def get_device_priority(device_id):
    device = devices.find_one(
        {"device_id": device_id}
    )

    if device is None:
        return None

    return device.get("priority")


def create_priority_request(device_id, requested_priority, reason, data):
    request = {
        "device_id": device_id,
        "requested_priority": requested_priority,
        "reason": reason,
        "data": data,
        "status": "pending",
        "created_at": datetime.now()
    }

    result = priority_requests.insert_one(request)

    print(
        f"Priority request created | "
        f"Request ID: {result.inserted_id}"
    )

    return result.inserted_id

def get_pending_priority_requests():
    return priority_requests.find(
        {"status": "pending"}
    )

def update_device_activity(device_id, sensor):
    current_time = datetime.now()

    devices.update_one(
        {"device_id": device_id},
        {
            "$set": {
                "status": "Online",
                "last_seen": current_time,
                "sensor": sensor
            }
        }
    )

def approve_priority_request(request_id):
    from bson.objectid import ObjectId

    request = priority_requests.find_one(
        {
            "_id": ObjectId(request_id),
            "status": "pending"
        }
    )

    if request is None:
        return None

    priority_requests.update_one(
        {
            "_id": ObjectId(request_id),
            "status": "pending"
        },
        {
            "$set": {
                "status": "approved",
                "approved_at": datetime.now()
            }
        }
    )

    return request["data"]


def deny_priority_request(request_id):
    from bson.objectid import ObjectId

    result = priority_requests.update_one(
        {"_id": ObjectId(request_id), "status": "pending"},
        {
            "$set": {
                "status": "denied",
                "denied_at": datetime.now()
            }
        }
    )

    return result.modified_count > 0


def get_approved_priority_requests():
    return priority_requests.find(
        {"status": "approved"}
    )


def mark_priority_request_queued(request_id):
    from bson.objectid import ObjectId

    priority_requests.update_one(
        {
            "_id": ObjectId(request_id),
            "status": "approved"
        },
        {
            "$set": {
                "status": "queued",
                "queued_at": datetime.now()
            }
        }
    )
from queue import PriorityQueue
from database import save_sensor_data, register_device, get_approved_priority_requests, mark_priority_request_queued
from monitor import message_processed, print_statistics_periodically

import threading
import time


message_queue = PriorityQueue()

message_counter = 0


def add_message(data):
    global message_counter

    message_counter += 1

    if data["priority"]=="high":
        priority = 1
    else:
        priority = 2

    message_queue.put((priority,message_counter,data))

    print(f"Message added to queue | Device : {data['device_id']} | Priority : {data['priority']}")


def process_message(data):
    message_processed()
    print(f"Processing message | Device : {data['device_id']} | Priority : {data['priority']} | Value : {data['value']}")

    save_sensor_data(data)

    register_device(data["device_id"], data["sensor"])

def process_messages():
    while True:
        priority, message_number, data = message_queue.get()
        process_message(data)

        message_queue.task_done()

def start_message_processor():
    processor_thread = threading.Thread(target=process_messages, daemon=True)

    processor_thread.start()

    monitor_thread = threading.Thread(target=print_statistics_periodically,args=(message_queue,) , daemon=True)

    monitor_thread.start()

    approval_thread = threading.Thread(target=check_approved_requests,daemon=True)

    approval_thread.start()

def check_approved_requests():
    while True:

        requests = list(get_approved_priority_requests())

        for request in requests:

            data = request["data"]

            print(
                f"Approved request received | "
                f"Device: {data['device_id']}"
            )

            add_message(data)

            mark_priority_request_queued(
                str(request["_id"])
            )

        time.sleep(2)
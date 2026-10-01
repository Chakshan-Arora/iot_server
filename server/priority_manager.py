from queue import PriorityQueue, Empty
from database import save_sensor_data, save_sensor_data_batch, register_device, get_approved_priority_requests, mark_priority_request_queued
from monitor import message_processed, print_statistics_periodically

import threading
import time


message_queue = PriorityQueue()


active_workers = 1
MAX_WORKERS = 5

counter_lock = threading.Lock()
timer_lock = threading.Lock()
worker_condition = threading.Condition()
register_lock = threading.Lock()

last_registered = {}
REGISTER_INTERVAL = 10

BATCH_SIZE = 50

benchmark_start = None
EXPECTED_MESSAGES = 1000
completed_messages = 0
benchmark_finished = False


message_counter = 0


def add_message(data):
    global message_counter

    with counter_lock:
        message_counter += 1
        current_counter = message_counter

    if data["priority"]=="high":
        priority = 1
    else:
        priority = 2

    message_queue.put((priority,current_counter,data))

    print(f"Message added to queue | Device : {data['device_id']} | Priority : {data['priority']}")

db_times = []

def process_batch(datas):
    save_sensor_data_batch(datas)
    print(f"Saved batch of {len(datas)} messages to MongoDB")

    now = time.monotonic()
    to_register = {}
    with register_lock:
        for d in datas:
            device_id = d["device_id"]
            last = last_registered.get(device_id)
            if last is None or now - last >= REGISTER_INTERVAL:
                last_registered[device_id] = now
                to_register[device_id] = d["sensor"]

    for device_id, sensor in to_register.items():
        register_device(device_id, sensor)

    for _ in datas:
        message_processed()


def process_messages(worker_id):
    global benchmark_start, completed_messages, benchmark_finished
    while True:

        with worker_condition:
            while worker_id >= active_workers:
                worker_condition.wait()

        batch = [message_queue.get()]
        while len(batch) < BATCH_SIZE:
            try:
                batch.append(message_queue.get_nowait())
            except Empty:
                break

        with timer_lock:
            if benchmark_start is None:
                benchmark_start = time.perf_counter()

        try:
            process_batch([item[2] for item in batch])

        except Exception as e:
            print(f"Error processing batch: {e}")

        finally:
            for _ in batch:
                message_queue.task_done()

            with timer_lock:
                completed_messages += len(batch)

                if (completed_messages >= EXPECTED_MESSAGES
                        and not benchmark_finished):
                    elapsed_time = time.perf_counter() - benchmark_start
                    benchmark_finished = True

                    print("\n--- Benchmark Results ---")
                    print(f"Workers: {active_workers}")
                    print(f"Messages completed: {completed_messages}")
                    print(f"Total processing time: {elapsed_time:.2f} seconds")
                    print(
                        f"Throughput: "
                        f"{completed_messages / elapsed_time:.2f} messages/sec"
                    )
                    print("-------------------------\n")

# def process_message(data):

#     # time.sleep(0.083)
    
#     # print(f"Processing message | Device : {data['device_id']} | Priority : {data['priority']} | Value : {data['value']}")

#     t0 = time.perf_counter()
#     save_sensor_data(data)
#     # t1 = time.perf_counter()
#     device_id = data["device_id"]

#     now = time.monotonic()
#     with register_lock:
#         last = last_registered.get(device_id)
#         due = last is None or now - last >= REGISTER_INTERVAL
#         if due:
#             last_registered[device_id] = now

#     if due:
#         register_device(data["device_id"], data["sensor"])
#     # t2 = time.perf_counter()
#     # print(f"timing | save: {t1 - t0:.3f}s | register: {t2 - t1:.3f}s")
#     db_times.append(time.perf_counter() - t0)
#     message_processed()

# def process_messages(worker_id):
#     global benchmark_start, completed_messages, benchmark_finished
#     while True:

#         with worker_condition:
#             while worker_id >= active_workers:
#                 worker_condition.wait()

#         priority, message_number, data = message_queue.get()

#         with timer_lock:
#             if benchmark_start is None:
#                 benchmark_start = time.perf_counter()

#         try:
#             process_message(data)

#         except Exception as e:
#             print(f"Error processing message: {e}")

#         finally:
#             message_queue.task_done()

#             with timer_lock:
#                 completed_messages += 1

#                 if (completed_messages == EXPECTED_MESSAGES
#                         and not benchmark_finished):
#                     elapsed_time = time.perf_counter() - benchmark_start
#                     benchmark_finished = True

#                     print("\n--- Benchmark Results ---")
#                     print(f"Workers: {active_workers}")
#                     print(f"Messages completed: {completed_messages}")
#                     print(f"Total processing time: {elapsed_time:.2f} seconds")
#                     print(
#                         f"Throughput: "
#                         f"{completed_messages / elapsed_time:.2f} messages/sec"
#                     )
#                     times = sorted(db_times)
#                     n = len(times)
#                     print(f"DB time/msg | mean : {sum(times)/n:.3f}s | median : {times[n//2]:.3f}s | min : {times[0]:.3f}s | max : {times[-1]:.3f}s")
                    
#                     print("-------------------------\n")


def adjust_workers():
    global active_workers

    while True:
        queue_size = message_queue.qsize()
        # print(f"QUEUE SIZE: {queue_size}")

        # Decide how many workers are needed
        if queue_size <= 10:
            new_worker_count = 1
        elif queue_size <= 50:
            new_worker_count = 2
        elif queue_size <= 100:
            new_worker_count = 3
        elif queue_size <= 200:
            new_worker_count = 4
        else:
            new_worker_count = 5

        new_worker_count = 5

        # Update the number of active workers
        with worker_condition:
            if new_worker_count != active_workers:
                active_workers = new_worker_count

                print(
                    f"Worker allocation changed | "
                    f"Active workers: {active_workers} | "
                    f"Queue size: {queue_size}"
                )

                worker_condition.notify_all()

        time.sleep(0.5)



def start_message_processor():

    # Start the maximum number of worker threads
    for i in range(MAX_WORKERS):
        processor_thread = threading.Thread(
            target=process_messages,
            args=(i,),
            daemon=True
        )
        processor_thread.start()
        print(f"Worker {i + 1} created")

    # Start dynamic worker controller
    worker_manager_thread = threading.Thread(
        target=adjust_workers,
        daemon=True
    )
    worker_manager_thread.start()

    # Start monitoring
    monitor_thread = threading.Thread(
        target=print_statistics_periodically,
        args=(message_queue,),
        daemon=True
    )
    monitor_thread.start()

    # Start admin approval polling
    approval_thread = threading.Thread(
        target=check_approved_requests,
        daemon=True
    )
    approval_thread.start()

def check_approved_requests():
    while True:
        try:
            for request in list(get_approved_priority_requests()):
                data = request["data"]
                print(f"Approved request received | Device: {data['device_id']}")
                add_message(data)
                mark_priority_request_queued(str(request["_id"]))
        except Exception as e:
            print(f"Approval poller error: {e}")
        time.sleep(2)
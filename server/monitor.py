import time

messages_received = 0
messages_processed = 0
messages_rejected = 0

high_priority_messages = 0
normal_priority_messages = 0

start_time = time.time()


def message_received():
    global messages_received
    messages_received += 1


def message_processed():
    global messages_processed
    messages_processed += 1


def message_rejected():
    global messages_rejected
    messages_rejected += 1


def priority_message(priority):

    global high_priority_messages
    global normal_priority_messages

    if priority == "high":
        high_priority_messages += 1

    else:
        normal_priority_messages += 1


def show_statistics(queue_size):

    running_time = time.time() - start_time

    print("\n--- Server Statistics ---")

    print(f"Running time: {running_time:.2f} seconds")
    print(f"Messages received: {messages_received}")
    print(f"Messages processed: {messages_processed}")
    print(f"Messages rejected: {messages_rejected}")

    print(f"High priority: {high_priority_messages}")
    print(f"Normal priority: {normal_priority_messages}")

    print(f"Current queue size: {queue_size}")

    print("-------------------------\n")

def print_statistics_periodically(queue):
    while True:
        time.sleep(120)

        show_statistics(queue.qsize())
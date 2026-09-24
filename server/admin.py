from database import (
    get_pending_priority_requests,
    approve_priority_request,
    deny_priority_request
)

from priority_manager import add_message


def show_pending_requests():
    requests = list(get_pending_priority_requests())

    if not requests:
        print("\nNo pending priority requests.\n")
        return

    print("\n--- Pending Priority Requests ---")

    for request in requests:
        print(f"\nRequest ID: {request['_id']}")
        print(f"Device: {request['device_id']}")
        print(f"Requested priority: {request['requested_priority']}")
        print(f"Reason: {request['reason']}")
        print(f"Created at: {request['created_at']}")

    print("\n--------------------------------")


def handle_request():
    show_pending_requests()

    request_id = input("\nEnter Request ID: ").strip()

    if not request_id:
        return

    choice = input(
        "Enter A to allow once or D to deny: "
    ).strip().lower()

    if choice == "a":
        data = approve_priority_request(request_id)

        if data is not None:
            print("Priority request approved.")
            print("Server will process approved message")
        else:
            print("Request not found or already handled.")

    elif choice == "d":
        success = deny_priority_request(request_id)

        if success:
            print("Priority request denied.")
        else:
            print("Request not found or already handled.")

    else:
        print("Invalid choice.")
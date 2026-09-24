from mqtt_handler import start_mqtt
from device_manager import start_device_monitor
from priority_manager import start_message_processor

print("Starting Server.....")
start_device_monitor()
start_message_processor()
start_mqtt()
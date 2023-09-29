import time
import ubinascii
from utils_umqtt import MQTTClient
import machine
import network
import random

from secrets import MQTT_BROKER, MQTT_CLIENT_ID
from utils_influxdb import build_payload


# CLIENT_ID = ubinascii.hexlify(machine.unique_id())
PUBLISH_TOPIC = b"forward2influxdb"
# SUBSCRIBE_TOPIC = b"led"

# Setup built in PICO LED as Output
# led = machine.Pin("LED", machine.Pin.OUT)

# Publish MQTT messages after every set timeout
# last_publish = time.time()
# publish_interval = 5


# Received messages from subscriptions will be delivered to this callback
# def sub_cb(topic, msg):
#     print((topic, msg))
#     if msg.decode() == "ON":
#         led.value(1)
#     else:
#         led.value(0)


mqttClient = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, keepalive=30)


def connect():
    # mqttClient.set_callback(sub_cb)
    print(f"Begin connection with MQTT Broker :: {MQTT_BROKER}")
    mqttClient.connect()
    # mqttClient.subscribe(SUBSCRIBE_TOPIC)
    # mqttClient.publish(SUBSCRIBE_TOPIC, "Off")
    print(
        f"Connected to MQTT  Broker :: {MQTT_BROKER}, and waiting for callback function to be called!"
    )
    # while True:
    #     # Non-blocking wait for message
    #     mqttClient.check_msg()
    #     global last_publish
    #     if (time.time() - last_publish) >= publish_interval:
    #         measurements = [
    #             {
    #                 "measurement": "dryer_A",  # a measurement has one 'measurement'. It is the name of the pcb.
    #                 "fields": {
    #                     "temperature_C": f"{random.randint(170, 220)/10.0:0.1f}",
    #                     "humidity_pRH": "88.2",
    #                 },
    #                 "tags": {
    #                     "setup": "zeus",
    #                     "room": "B15",
    #                 },
    #             },
    #             {
    #                 "measurement": "dryer_B",  # a measurement has one 'measurement'. It is the name of the pcb.
    #                 "fields": {
    #                     "temperature_C": f"{random.randint(230, 290)/10.0:0.1f}",
    #                     "humidity_pRH": "45.6",
    #                 },
    #                 "tags": {
    #                     "setup": "zeus",
    #                     "room": "B16",
    #                 },
    #             },
    #         ]
    #         payload = build_payload(measurements)
    #         print(f"{MQTT_BROKER}: {PUBLISH_TOPIC}")
    #         print(payload)
    #         mqttClient.publish(PUBLISH_TOPIC, payload)
    #         last_publish = time.time()
    #     time.sleep(1)


def publish(fields: dict) -> None:
    measurements = [
        {
            "measurement": MQTT_CLIENT_ID,  # a measurement has one 'measurement'. It is the name of the pcb.
            "fields": fields,
            "tags": {
                "setup": "zeus",
                "room": "B15",
            },
        },
    ]
    payload = build_payload(measurements)
    if False:
        print(f"{MQTT_BROKER}: {PUBLISH_TOPIC}")
        print(payload)
    mqttClient.publish(PUBLISH_TOPIC, payload)

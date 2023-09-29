import time
import ubinascii
from umqtt.simple import MQTTClient
import machine
import random

# Default  MQTT_BROKER to connect to
MQTT_BROKER = "maerki.com"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
PUBLISH_TOPIC = b"temperature"
PUBLISH_TOPIC = b"mosquitto/temperature/5"
PUBLISH_TOPIC = b"mosquitto/temperature/1a97"
SUBSCRIBE_TOPIC = b"led"

# Setup built in PICO LED as Output
led = machine.Pin("LED",machine.Pin.OUT)

# Publish MQTT messages after every set timeout
last_publish = time.time()
publish_interval = 5

# Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg):
    print((topic, msg))
    if msg.decode() == "ON":
        led.value(1)
    else:
        led.value(0)


def reset():
    print("Resetting...")
    time.sleep(5)
    machine.reset()
    
# Generate dummy random temperature readings    
def get_temperature_reading():
    return random.randint(20, 50)
    
def main():
    print(f"Begin connection with MQTT Broker :: {MQTT_BROKER}")
    mqttClient = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
    mqttClient.set_callback(sub_cb)
    mqttClient.connect()
    mqttClient.subscribe(SUBSCRIBE_TOPIC)
    print(f"Connected to MQTT  Broker :: {MQTT_BROKER}, and waiting for callback function to be called!")
    while True:
            # Non-blocking wait for message
            mqttClient.check_msg()
            global last_publish
            if (time.time() - last_publish) >= publish_interval:
                random_temp = get_temperature_reading()
                # print(f"{MQTT_BROKER}: {PUBLISH_TOPIC}: {str(random_temp).encode()}")
                # mqttClient.publish(PUBLISH_TOPIC, str(random_temp).encode())
                # https://github.com/influxdata/telegraf/blob/master/plugins/parsers/json_v2/testdata/timestamp/input.json
                payload = b"25.5"
                # https://www.mikrocontroller.net/topic/545947
                # Topic sensors/1a97/msg
                # payload = b"""{"Id":"1a97","Time":"1668545893","Temperature":"+11.3","Humidity":"86","Battery":"0","RSSI":"79"}"""
                print(f"{MQTT_BROKER}: {PUBLISH_TOPIC}: {payload}")
                mqttClient.publish(PUBLISH_TOPIC, payload)
                last_publish = time.time()
            time.sleep(1)


if __name__ == "__main__":
    while True:
        try:
            main()
        except OSError as e:
            print("Error: " + str(e))
            reset()


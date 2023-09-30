import time
import network
from utils_umqtt import MQTTClient

import secrets
import utils_influxdb


class WLAN:
    def __init__(self):
        self.sta_fi = None

    def _find_ssid(self):
        """
        returns (ssid, password)
        or (None, None)
        """
        for ssid, bssid, channel, RSSI, security, hidden in self.sta_fi.scan():
            for _ssid, password in secrets.SSID_CREDENTIALS:
                assert isinstance(_ssid, bytes), _ssid
                # print("ssid", ssid, _ssid)
                if ssid == _ssid:
                    return (_ssid, password)
        else:
            print("WARNING: WLANs.scan() returned empty list!")
        return (None, None)

    def connect(self) -> bool:
        """
        Return True if connected
        """
        try:
            if self.sta_fi is None:
                self.sta_fi = network.WLAN(network.STA_IF)
                self.sta_fi.active(True)

            if self.sta_fi.isconnected():
                return True
            ssid, password = self._find_ssid()
            if ssid is None:
                print("No known SSID!")
                return False
            print(f"connecting WLAN '{ssid:s}' ...")
            self.sta_fi.connect(ssid, password)
            timeout_ms = 10000
            start_ms = time.ticks_ms()
            while not self.sta_fi.isconnected():
                time.sleep(1)
                duration_ms = time.ticks_diff(time.ticks_ms(), start_ms)
                if duration_ms > timeout_ms:
                    print(f"Timeout of {timeout_ms}ms while waiting for connection!")
                    return False
            print("Connected! Network config:", self.sta_fi.ifconfig())
            return True
        except OSError as e:
            print(f"ERROR: wlan.connect() failed: {e}")
            return False

    def disconnect(self):
        self.sta_fi.disconnect()
        # self.sta_fi = None


# CLIENT_ID = ubinascii.hexlify(machine.unique_id())
PUBLISH_TOPIC = b"forward2influxdb"
INITIAL_VALUE = b"dummy"


class MQTT:
    def __init__(self, wlan: WLAN):
        self.client = None
        self.wlan = wlan
        self._callbacks = {}

    # def create_subscribe_topic(self, subtopic: str) -> bytes:
    #     return f"filament_driver/{MQTT_CLIENT_ID}/{subtopic}".encode()
    def register_callback(self, subtopic: str, cb):
        topic = f"filament_driver/{secrets.MQTT_CLIENT_ID}/{subtopic}".encode()
        self._callbacks[topic] = cb

    def _callback(self, topic: bytes, msg: bytes):
        if msg == INITIAL_VALUE:
            return
        cb = self._callbacks.get(topic, None)
        if cb is None:
            print(f"Topic '{topic}' was not registered!")
            return
        cb(msg.decode("ascii"))

    def connect(self):
        if not self.wlan.connect():
            return
        if self.client is None:
            self.client = MQTTClient(
                secrets.MQTT_CLIENT_ID,
                secrets.MQTT_BROKER,
                user=secrets.MQTT_BROKER_USER,
                password=secrets.MQTT_BROKER_PW,
                keepalive=30,
            )
        if self.client.sock is not None:
            # We are already connected
            return True
        self.client.set_callback(self._callback)
        print(f"MQTT Broker {secrets.MQTT_BROKER}")
        try:
            self.client.connect()
        except OSError as e:
            print(f"ERROR: MQTT connect() failed: {e}")
            return False
        # self.client.subscribe(SUBSCRIBE_TOPIC)
        # self.client.publish(SUBSCRIBE_TOPIC, "Off")
        for topic in self._callbacks:
            self.client.subscribe(topic)
            self.client.publish(topic, INITIAL_VALUE)

        return True

    def publish(self, fields: dict) -> None:
        if not self.connect():
            return
        measurements = [
            {
                "measurement": secrets.MQTT_CLIENT_ID,  # a measurement has one 'measurement'. It is the name of the pcb.
                "fields": fields,
                "tags": {
                    "setup": "zeus",
                    "room": "B15",
                },
            },
        ]
        payload = utils_influxdb.build_payload(measurements)
        if False:
            print(f"{MQTT_BROKER}: {PUBLISH_TOPIC}")
            print(payload)
        try:
            self.client.publish(PUBLISH_TOPIC, payload)
        except OSError as e:
            print(f"ERROR: MQTT publish() failed: {e}")
            self.wlan.disconnect()
            return
        try:
            self.client.check_msg()
        except OSError as e:
            print(f"ERROR: MQTT check_msg() failed: {e}")
            self.wlan.disconnect()
            return

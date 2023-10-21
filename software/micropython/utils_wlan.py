import time
import rp2
import network
from utils_umqtt import MQTTClient

import secrets
import utils_influxdb

# https://github.com/micropython/micropython/issues/11977
country = const("CH")
rp2.country(country)
network.country(country)


WLAN_CONNECT_TIME_OUT_MS = const(10000)


class WLAN:
    def __init__(self):
        self._wdt_feed = lambda: False
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.config(pm=network.WLAN.PM_PERFORMANCE)
        self.connection_counter = 0
        # time.sleep(1.0)
        # print(f"DEBUG: reset 2: {self._wlan.isconnected()}, {self._wlan.status()}")

    def register_wdt_feed_cb(self, wdt_feed_cb):
        """
        When using the wdt, using this callbac, this WLAN class
        will call the watchdog whenever possible.
        """
        self._wdt_feed = wdt_feed_cb

    def power_on(self) -> None:
        """
        Power of the WLAN interface
        """
        # print(f"DEBUG: interface_start 1: {self.status_text}")
        self._wlan.active(True)
        # print(f"DEBUG: interface_start 2: {self.status_text}")

    def power_off(self) -> None:
        """
        Power off the WLAN
        https://github.com/orgs/micropython/discussions/10889

        Sometimes a WLAN connection is dangeling in a unwanted state.
        `power_off()` normally recovers and allows us to create a brand
        new connection.
        """
        # print(f"DEBUG: interface_stop 1: {self.status_text}")
        self._wlan.disconnect()
        # print(f"DEBUG: interface_stop 2: {self.status_text}")
        self._wlan.active(False)
        # print(f"DEBUG: interface_stop 3: {self.status_text}")
        self._wlan.deinit()
        # print(f"DEBUG: interface_stop 4: {self.status_text}")

    def get_status_name(self, status: int):
        """
        Returns the text related to `_wlan.status()`
        """
        for k, v in network.__dict__.items():
            if k.startswith("STAT_"):
                if v == status:
                    return k
        return "??"

    @property
    def status_text(self):
        """
        Returns a summary text for the wlan interface
        """
        status = self._wlan.status()
        return f"isconnected: {self._wlan.isconnected()}, status: {status}({self.get_status_name(status)}), ip_address: {self.ip_address}"

    @property
    def ip_address(self):
        return self._wlan.ifconfig()[0]

    def _find_ssid(self):
        """
        returns (ssid, password)
        or (None, None)
        """
        # Scan the wlan
        self._wdt_feed()
        set_ssids = {l[0] for l in self._wlan.scan()}

        if len(set_ssids) == 0:
            print("WARNING: WLANs.scan() returned empty list!")
            return (None, None)

        for ssid, password in secrets.SSID_CREDENTIALS:
            assert isinstance(ssid, bytes), ssid
            assert isinstance(password, str), password
            if ssid in set_ssids:
                print(f"DEBUG: selected network: {ssid}")
                return (ssid, password)

        print("WARNING: WLANs.scan(): No matching network seen!")
        return (None, None)

    @property
    def ip_address(self):
        return self._wlan.ifconfig()[0]

    @property
    def got_ip_address(self) -> bool:
        """
        Return True if we have a ip address assigned.
        IMPORTANT: Even we do not generated ip traffic, `got_ip_address` will return False
        in about 5s after the AP dissapeared.
        So this is a good indication if the WLAN connection is lost.
        """
        if not self._wlan.isconnected():
            return False
        return self.ip_address != "0.0.0.0"

    def connect(self) -> bool:
        """
        Return True if connection could be established
        """
        try:
            if self.got_ip_address:
                return True
            print(f"DEBUG: connecting WLAN ...")
            self._wdt_feed()
            self.power_off()
            time.sleep(1)
            self.power_on()
            ssid, password = self._find_ssid()
            if ssid is None:
                # print("WARNING: No known SSID!")
                return False
            print(f"DEBUG: connecting WLAN '{ssid:s}' ...")
            self._wdt_feed()
            self._wlan.connect(ssid, password)
            start_ms = time.ticks_ms()
            while True:
                self._wdt_feed()
                duration_ms = time.ticks_diff(time.ticks_ms(), start_ms)
                if self.got_ip_address:
                    break
                if duration_ms > WLAN_CONNECT_TIME_OUT_MS:
                    print(
                        f"WARNING: Timeout of {duration_ms}ms while waiting for connection!"
                    )
                    return False
                time.sleep(1)
            print(
                f"DEBUG: Connected within {duration_ms}ms to {ssid} and ip {self.ip_address}"
            )
            self.connection_counter += 1
            return True
        except OSError as e:
            print(f"ERROR: wlan.connect() failed: {e}")
            return False


# CLIENT_ID = ubinascii.hexlify(machine.unique_id())
PUBLISH_TOPIC = b"forward2influxdb"
INITIAL_VALUE = b"dummy"


class MQTT:
    def __init__(self, wlan: WLAN):
        self.client = None
        self.wlan = wlan
        self._callbacks = {}
        self.wlan_connection_counter = -1

    def register_callback(self, subtopic: str, cb):
        topic = f"filament_dryer/{secrets.MQTT_CLIENT_ID}/{subtopic}".encode()
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
            return False
        # print("DEBUG: MQTT connect...")
        if self.wlan_connection_counter == self.wlan.connection_counter:
            return True
        print(
            f"DEBUG: WLAN reconnected (connection_counter:{self.wlan.connection_counter}). MQTT has to reconnect too..."
        )
        self.client = None
        self.wlan_connection_counter = self.wlan.connection_counter

        if self.client is None:
            self.wlan._wdt_feed()
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
        self.wlan._wdt_feed()
        self.client.set_callback(self._callback)
        # print(f"DEBUG: MQTT Broker '{secrets.MQTT_BROKER}'")
        try:
            self.wlan._wdt_feed()
            self.client.connect()
        except OSError as e:
            print(f"ERROR: MQTT connect() failed: {e}")
            return False
        # self.client.subscribe(SUBSCRIBE_TOPIC)
        # self.client.publish(SUBSCRIBE_TOPIC, "Off")
        for topic in self._callbacks:
            self.wlan._wdt_feed()
            self.client.subscribe(topic)
            self.wlan._wdt_feed()
            self.client.publish(topic, INITIAL_VALUE)

        # Avoid recursion!
        # self.wlan._wdt_feed()
        # self.publish_annotation(title="WLAN", text="connected")
        self._last_access_ms = time.ticks_ms()
        print(f"DEBUG: MQTT connected to {secrets.MQTT_BROKER}")
        return True

    def publish(self, fields: dict, tags: dict) -> None:
        if not self.connect():
            return
        tags["setup"] = "zeus"
        tags["room"] = "B15"
        measurements = [
            {
                "measurement": secrets.MQTT_CLIENT_ID,  # a measurement has one 'measurement'. It is the name of the pcb.
                "fields": fields,
                "tags": tags,
            },
        ]
        payload = utils_influxdb.build_payload(measurements)
        if False:
            print(f"{MQTT_BROKER}: {PUBLISH_TOPIC}")
            print(payload)
        try:
            self.wlan._wdt_feed()
            self.client.publish(PUBLISH_TOPIC, payload)
        except OSError as e:
            print(f"ERROR: MQTT publish() failed: {e}")
            self.wlan.power_off()
            return
        try:
            self.wlan._wdt_feed()
            self.client.check_msg()
        except OSError as e:
            print(f"ERROR: MQTT check_msg() failed: {e}")
            self.wlan.power_off()
            return

    def publish_annotation(self, title: str, text: str, severity="INFO") -> None:
        fields = {
            "title": f'"{title}"',
            "text": f'"{text}"',
        }
        tags = {
            "severity": severity,
            "event": "annotation",
        }
        self.publish(fields=fields, tags=tags)

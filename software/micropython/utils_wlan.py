import time
import ubinascii
import machine
import network
import random

from secrets import MQTT_BROKER, SSID, SSID_PASSWORD

from utils_influxdb import build_payload


sta_if = network.WLAN(network.STA_IF)

def connect():
    if sta_if.isconnected():
        return
    print("connecting to network...")
    sta_if.active(True)
    for ap in sta_if.scan():
        print(f"scan: {ap}")
    sta_if.connect(SSID, SSID_PASSWORD)
    while not sta_if.isconnected():
        print("Attempting to connect....")
        time.sleep(1)
    print("Connected! Network config:", sta_if.ifconfig())



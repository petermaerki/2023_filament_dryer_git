import rp2
import time
import network

country = const("CH")
rp2.country(country)
network.country(country)

wlan = network.WLAN(network.STA_IF)
wlan.config(pm=network.WLAN.PM_PERFORMANCE)


def get_status_name(status: int):
    for k, v in network.__dict__.items():
        if k.startswith("STAT_"):
            if v == status:
                return k
    return "??"


def status_text():
    status = wlan.status()
    ip_address = wlan.ifconfig()[0]
    return f"isconnected: {wlan.isconnected()}, status: {status}({get_status_name(status)}), ip_address: {ip_address}"


def connect():
    print("connect before")
    wlan.connect(b"TempStabilizer2018", "wmm_enabled")
    # wlan.connect(b"mi", "karlheinZ76")
    print("connect after 1")
    while not wlan.isconnected():
        print(status_text())
        time.sleep(1)
    print("connect after 2")
    print(status_text())


def c():
    print(status_text())
    wlan.active(True)
    # time.sleep(2)
    # print(status_text())
    # wlan.active(True)
    # time.sleep(2)
    print(status_text())
    connect()


def d():
    # https://github.com/orgs/micropython/discussions/10889
    print(status_text())
    wlan.disconnect()
    wlan.active(False)
    wlan.deinit()
    print(status_text())
    time.sleep(1)
    print(status_text())

import time
import machine
import utils_wlan

from utils_constants import DURATION_H_MS

WLAN_RECONNECT_RETRY_MS = DURATION_H_MS
WLAN_REBOOT_MS = 2*DURATION_H_MS

def main_core1():
    """
    The first core
    * connects to WLAN
    * reboots if WLAN was down for WLAN_REBOOT_MS
    """
    print("DEBUG: main_core1: started")
    while True:
        wlan.power_off()

        print("********************** UP")
        start_s = time.time()
        print("INFO: main_core1: 1")
        wlan.power_on()
        print("INFO: main_core1: 2")
        success = wlan.connect()
        print(f"INFO: main_core1: success={success} {time.time()-start_s}s")

        print("********************** Test")
        for i in range(20):
            print(f"{i}: {wlan.status_text}")
            if not wlan.got_ip_address:
                break
            time.sleep(1)

        # print("********************** DOWN")
        # print(f"INFO: main_core1: interface_stop() {time.time()-start_s}s")
        # wlan.power_off()
        # time.sleep(2)


wlan = utils_wlan.WLAN()
if True:
    main_core1()

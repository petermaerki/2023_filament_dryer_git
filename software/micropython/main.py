import os
import rp2
import os
import gc
import time
import machine
import micropython
import _thread


micropython.alloc_emergency_exception_buf(100)

import utils_wlan

import utils_button
import utils_wlan
from utils_wdt import wdt
from utils_logstdout import logfile
from utils_log import LogfileTags
from utils_timebase import tb
from mod_hardware import Hardware
from mod_sensoren import Sensoren
from mod_statemachine import Statemachine
from utils_constants import DIRECTORY_LOGS, DURATION_H_MS


WLAN_RECONNECT_RETRY_MS = DURATION_H_MS
WLAN_REBOOT_MS = 2*DURATION_H_MS

class Globals:
    def __init__(self):
        self.stdout = False
        self.stop_thread = False


g = Globals()

# wdt.enable()

hardware = Hardware()
sensoren = Sensoren(hardware=hardware)


sm = Statemachine(hardware=hardware, sensoren=sensoren)
sensoren.sensor_statemachine.set_sm(sm=sm)


# print(LogfileTags.SENSORS_HEADER)


def main_core2(mqtt):
    print("DEBUG: main_core2: started")

    def statechange(old: str, new: str, why: str) -> None:
        mqtt.publish_annotation(
            title=f"Statechange: {old} -> {new}", text=f"Why: {why}"
        )

    sm.statechange_cb = statechange

    def statemachine_cb(msg: str):
        print(f"statemachine_cb: {msg}")
        sm.switch_by_name(msg)

    mqtt.register_callback("statemachine", statemachine_cb)

    # logfile.log(LogfileTags.SENSORS_HEADER, sensoren.sensors.get_header())

    while True:
        sensoren.measure()

        sm.state()
        hardware.heater.set_board_C(board_C=sensoren.heater_C)

        # logfile.log(LogfileTags.LOG_DEBUG, f"{tb.sleep_done_ms}, {tb.sleep_done_ms}")
        logfile.log(
            LogfileTags.SENSORS_VALUES,
            sensoren.sensors.get_values(sensoren.stdout_measurements),
            stdout=g.stdout,
        )

        # print("get_mqtt_fields")
        # print(sensors.get_mqtt_fields())
        mqtt.publish(fields=sensoren.sensors.get_mqtt_fields())

        if g.stop_thread:
            logfile.log(LogfileTags.LOG_INFO, "Stopped", stdout=True)
            logfile.flush()
            return

        tb.sleep()

def main_core1():
    print("DEBUG: main_core1: started")
    wlan = utils_wlan.WLAN()
    mqtt = utils_wlan.MQTT(wlan)
    _thread.start_new_thread(main_core2, [mqtt])
    while True:
        print("DEBUG: main_core1: wlan.connect()")
        success = wlan.connect()
        print(f"DEBUG: main_core1: wlan.connect() returned {success}")
        if mqtt.duration_since_last_access_ms > WLAN_REBOOT_MS:
            print(f"Wlan or mqtt was down for {WLAN_REBOOT_MS}ms, so lets reboot and retry!")
            machine.reset()
        time.sleep(WLAN_RECONNECT_RETRY_MS)

def pressed(duration_ms: int) -> None:
    sm.set_forward_to_next_state()


def long_pressed(timer) -> None:
    # Hard reset micropython
    machine.reset()


utils_button.Button(
    hardware.PIN_GPIO_BUTTON,
    pressed_cb=pressed,
    cb_long_press=long_pressed,
    long_press_ms=2000,
    invers=True,
)


# PIN_GPIO_HEATER_A.value(1)
# PIN_GPIO_HEATER_B.value(1)
# PIN_GPIO_FAN_AMBIENT.value(1)
# PIN_GPIO_FAN_SILICAGEL.value(1)


def thread():
    _thread.start_new_thread(main_core2, ())


def values():
    print(sensoren.sensors.get_header(measurements=sensoren.stdout_measurements))
    print(sensoren.sensors.get_values(measurements=sensoren.stdout_measurements))


def valuesall():
    print(sensoren.sensors.get_header())
    print(sensoren.sensors.get_values())


# def main():
#     g.stdout = True
#     main_core2()


# def s0():
#     g.stdout = False


# def s1():
#     g.stdout = True
#     print(sensors.get_header())


# def fa():
#     PIN_GPIO_FAN_AMBIENT.toggle()


# def fs():
#     PIN_GPIO_FAN_SILICAGEL.toggle()


# def hd():
#     print(sensors.get_header())


# def h(power: bool):
#     heater.set_power(power=power)


# def stop():
#     g.stop_thread = True


def df():  # Disk Free
    print("*** Garbage")
    print(
        f"Allocated/Free {gc.mem_alloc()/1000.0:0.3f}/{gc.mem_free()/1000.0:0.3f} kBytes"
    )
    gc.collect()
    print(
        f"Allocated/Free {gc.mem_alloc()/1000.0:0.3f}/{gc.mem_free()/1000.0:0.3f} kBytes"
    )

    print("*** Filesystem")
    logfile.flush()
    (
        f_bsize,
        f_frsize,
        f_blocks,
        f_bfree,
        f_bavail,
        f_files,
        f_ffree,
        f_favail,
        f_flag,
        f_namemax,
    ) = os.statvfs(DIRECTORY_LOGS)
    print(f"File system size total:  {f_blocks*f_frsize/1024.0} kBytes")
    print(f"File system size free:  {f_bavail*f_bsize/1024.0} kBytes")
    print(f"File system inodes free:  {f_favail}/{f_ffree} inodes")

    # print("*** Logfiles")
    # for name, type, inode, size in os.ilistdir("logs"):
    #     print(f"{DIRECTORY_LOGS}/{name}: {size} bytes")


def format():  # Reformat
    hardware.heater.set_power(False)

    # https://www.i-programmer.info/programming/hardware/16334-raspberry-pi-pico-file-system-a-sd-card-reader.html?start=1
    flash = rp2.Flash()
    os.umount("/")
    os.VfsLfs2.mkfs(flash)
    os.mount(flash, "/")
    machine.soft_reset()


def smp():
    print(sm.state_name)


def smx(new_state: str):
    sm.switch_by_name(new_state)

# g.stdout = True
if True:
    main_core1()
else:
    _thread.start_new_thread(main_core2, ())

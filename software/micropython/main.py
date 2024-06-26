import rp2
import os
import gc
import machine
import micropython
import _thread


micropython.alloc_emergency_exception_buf(100)

import utils_button
import utils_wlan
import utils_constants
import config_secrets
from utils_wdt import wdt
from utils_logstdout import logfile
from utils_log import LogfileTags
from utils_timebase import tb
from mod_hardware import Hardware
from mod_sensoren import Sensoren
from mod_statemachine import Statemachine
from utils_app_package_poll import new_version_available, sw_version
from utils_constants import DIRECTORY_LOGS

ENABLE_APP_PACKAGE_UPDATE = True
ENABLE_WDT = True

boot_cause = {
    machine.PWRON_RESET: "power on",
    machine.WDT_RESET: "watchdog reset",
}.get(machine.reset_cause(), "soft reset")
print(f"Boot cause: {boot_cause} ({machine.reset_cause()})")

hardware = Hardware()

if ENABLE_WDT and (hardware.PIN_GPIO_BUTTON.value() == 1):
    wdt.enable()
    print("To disable the watchdog: Press the user button before power on...")
else:
    print("User button pressed: Watchdog disabled!")
    ENABLE_APP_PACKAGE_UPDATE = False
    wdt.disable()

# hardware.production_test(wdt.feed)
sensoren = Sensoren(hardware=hardware)

sm = Statemachine(hardware=hardware, sensoren=sensoren)
sensoren.sensor_statemachine.set_sm(sm=sm)


class AppPackage:
    def __init__(self):
        self.next_poll_ms = 0

    def poll(self):
        if not ENABLE_APP_PACKAGE_UPDATE:
            return

        if tb.now_ms < self.next_poll_ms:
            return

        self.next_poll_ms += 10 * utils_constants.DURATION_MIN_MS

        # version = "mpy_version/6.1"
        version = "src"
        dict_tar = new_version_available(version, wdt_feed=wdt.feed)

        if dict_tar is not None:
            # Upload late: We will reboot afterwords!
            from utils_app_package_download import download_new_version

            download_new_version(dict_tar, wdt_feed=wdt.feed)


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

    mqtt_first_time_counter = 0
    app_package = AppPackage()
    while True:
        hardware.led_toggle()
        sensoren.measure()
        hardware.led_toggle()

        sm.state()
        hardware.heater.set_board_C(board_C=sensoren.heater_C)

        # logfile.log(LogfileTags.LOG_DEBUG, f"{tb.sleep_done_ms}, {tb.sleep_done_ms}")
        logfile.log(
            LogfileTags.SENSORS_VALUES,
            sensoren.sensors.get_values(sensoren.stdout_measurements),
            stdout=False,
        )

        # Send two annotations within 20s
        if mqtt_first_time_counter == 1:
            if mqtt.publish_annotation(
                title="Software version",
                text=sw_version(),
            ):
                mqtt_first_time_counter += 1
        if mqtt_first_time_counter == 0:
            if mqtt.publish_annotation(
                title=f"Boot due to {boot_cause}",
                text=f"serial {config_secrets.HW_SERIAL}, {config_secrets.HW_VERSION}, {wlan.ip_address}",
            ):
                mqtt_first_time_counter += 1

        mqtt.publish(fields=sensoren.sensors.get_mqtt_fields(), tags={})

        if wlan.got_ip_address:
            app_package.poll()

        gc.collect()
        tb.sleep()


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


def thread():
    _thread.start_new_thread(main_core2, ())


def values():
    print(sensoren.sensors.get_header(measurements=sensoren.stdout_measurements))
    print(sensoren.sensors.get_values(measurements=sensoren.stdout_measurements))


def valuesall():
    print(sensoren.sensors.get_header())
    print(sensoren.sensors.get_values())


def power_off():
    wlan.power_off()


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


wlan = utils_wlan.WLAN()
wlan.register_wdt_feed_cb(wdt.feed)
# Make sure, the connection before the reboot is dropped.
wlan.power_off()
wlan.connect()
mqtt = utils_wlan.MQTT(wlan)

if True:
    main_core2(mqtt)
else:
    _thread.start_new_thread(main_core2, (mqtt,))

from machine import Pin, I2C, reset
import micropython
import os
import gc
import _thread

micropython.alloc_emergency_exception_buf(100)

import utils_wlan

import config
from utils_constants import DIRECTORY_LOGS
from utils_log import LogStdout, LogfileTags
import utils_button
from mod_hardware import Hardware, Heater
from mod_sensoren import Sensoren
from utils_time import Timebase
import utils_measurement


class Globals:
    def __init__(self):
        self.stdout = False
        self.stop_thread = False


g = Globals()


tb = Timebase(interval_ms=config.MEASURE_INTERVAL_MS)
logfile = LogStdout(timebase=tb)
utils_measurement.logfile = logfile

hardware = Hardware()
sensoren = Sensoren(hardware=hardware)


class Statemachine:
    PREFIX_STATE = "_state_"
    PREFIX_ENTRY = "_entry_"

    def __init__(self):
        self.state_name = "none"
        self._start_ms = 0

        self._regenrate_last_fanon_ms = 0
        self._dryfan_list_dew_C = []
        self._dryfan_next_ms = 0
        self._forward_to_next_state = False
        self.statechange_cb = lambda state, new_state, why: state
        self.state = self._state_off
        self._entry_off()

    def set_forward_to_next_state(self) -> None:
        self._forward_to_next_state = True
        self.state()

    @property
    def forward_to_next_state(self) -> bool:
        if self._forward_to_next_state:
            self._forward_to_next_state = False
            return True
        return False

    @property
    def duration_ms(self) -> int:
        return tb.now_ms - self._start_ms

    def switch_by_name(self, new_state: str) -> None:
        state_name = f"_state_{new_state}"
        print(f"state_name: '{state_name}'")
        try:
            state_func = getattr(self, state_name)
        except AttributeError as e:
            print(f"WARNING: Unexisting state '{state_name}'!")
            return
        self._switch(state_func, "MQTT intervention")

    def _switch(self, new_state, why: str) -> None:
        assert new_state.__name__.startswith(self.PREFIX_STATE)
        new_state_name = new_state.__name__.replace(self.PREFIX_STATE, "")
        if self.state_name == new_state_name:
            return
        msg = f"'{self.state_name}' -> '{new_state_name}' {why}"
        logfile.log(LogfileTags.SM_STATE, msg, stdout=True)
        self.statechange_cb(self.state_name, new_state_name, why)
        self.state_name = new_state_name
        self.state = new_state
        self._start_ms = tb.now_ms

        new_entry_name = self.PREFIX_ENTRY + new_state_name
        f_entry = getattr(self, new_entry_name)
        f_entry()

    # State: OFF
    def _entry_off(self) -> None:
        hardware.PIN_GPIO_FAN_AMBIENT.off()
        hardware.PIN_GPIO_FAN_SILICAGEL.off()
        hardware.heater.set_power(False)

        hardware.PIN_GPIO_LED_GREEN.value(1)
        hardware.PIN_GPIO_LED_RED.value(1)
        hardware.PIN_GPIO_LED_WHITE.value(1)

    def _state_off(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_regenerate, "Forward to next state")

    # State: REGENERATE
    def _entry_regenerate(self) -> None:
        self._regenrate_last_fanon_ms = 0
        hardware.PIN_GPIO_FAN_AMBIENT.off()
        hardware.PIN_GPIO_FAN_SILICAGEL.off()
        hardware.heater.set_power(True)

        hardware.PIN_GPIO_LED_GREEN.value(0)
        hardware.PIN_GPIO_LED_RED.value(1)
        hardware.PIN_GPIO_LED_WHITE.value(0)

    def _state_regenerate(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_cooldown, "Forward to next state")
            return

        # Controller for the fan
        diff_dew_C = (
            sensoren.sensor_sht31_heater.measurement_dew_C.value
            - sensoren.sensor_sht31_ambient.measurement_dew_C.value
        )
        fan_on = diff_dew_C > config.SM_REGENERATE_DIFF_DEW_C
        hardware.PIN_GPIO_FAN_AMBIENT.value(fan_on)

        if fan_on:
            self._regenrate_last_fanon_ms = tb.now_ms
            return

        # Do state change if fan was off for a 'long' time.
        if sensoren.sensor_ds18_heater.heater_C < config.SM_REGENERATE_HOT_C:
            self._regenrate_last_fanon_ms = tb.now_ms
            return

        duration_fan_off_ms = tb.now_ms - self._regenrate_last_fanon_ms
        assert duration_fan_off_ms >= 0
        if duration_fan_off_ms > config.SM_REGENERATE_NOFAN_MS:
            why = f"duration_fan_off_ms {duration_fan_off_ms}ms > SM_REGENERATE_NOFAN_MS {config.SM_REGENERATE_NOFAN_MS}ms"
            self._switch(self._state_cooldown, why)

    # State: COOL DOWN
    def _entry_cooldown(self) -> None:
        hardware.PIN_GPIO_FAN_SILICAGEL.off()
        hardware.PIN_GPIO_FAN_AMBIENT.off()
        hardware.heater.set_power(False)

        hardware.PIN_GPIO_LED_GREEN.value(0)
        hardware.PIN_GPIO_LED_RED.value(1)
        hardware.PIN_GPIO_LED_WHITE.value(1)

    def _state_cooldown(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_dryfan, "Forward to next state")
            return

        heater_C = sensoren.sensor_ds18_heater.heater_C
        if heater_C < config.SM_COOLDOWN_TEMPERATURE_HEATER_C:
            self._switch(
                self._state_dryfan,
                f"heater_C {heater_C:0.1f}C < SM_COOLDOWN_TEMPERATURE_HEATER_C {config.SM_COOLDOWN_TEMPERATURE_HEATER_C:0.1f}C",
            )

    # State: DRY FAN
    def _entry_dryfan(self) -> None:
        hardware.PIN_GPIO_FAN_SILICAGEL.on()
        hardware.PIN_GPIO_FAN_AMBIENT.off()
        hardware.heater.set_power(False)
        self._dryfan_list_dew_C = []
        self._dryfan_next_ms = tb.now_ms

        hardware.PIN_GPIO_LED_GREEN.value(0)
        hardware.PIN_GPIO_LED_RED.value(0)
        hardware.PIN_GPIO_LED_WHITE.value(1)

    def _state_dryfan(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_drywait, "Forward to next state")
            return

        if tb.now_ms >= self._dryfan_next_ms:
            logfile.log(
                LogfileTags.LOG_INFO,
                f"len={len(self._dryfan_list_dew_C)}, append({sensoren.sensor_sht31_filament.measurement_dew_C.value})",
                stdout=True,
            )
            self._dryfan_next_ms += config.SM_DRYFAN_NEXT_MS
            self._dryfan_list_dew_C.insert(
                0, sensoren.sensor_sht31_filament.measurement_dew_C.value
            )

            if len(self._dryfan_list_dew_C) > config.SM_DRYFAN_ELEMENTS:
                reduction_dew_C = (
                    self._dryfan_list_dew_C[-1] - self._dryfan_list_dew_C[0]
                )
                logfile.log(
                    LogfileTags.LOG_INFO,
                    f"reduction_dew_C={reduction_dew_C:0.1f}",
                    stdout=True,
                )
                self._dryfan_list_dew_C.pop()
                if reduction_dew_C < config.SM_DRYFAN_DIFF_DEW_C:
                    why = f"reduction_dew_C {reduction_dew_C:0.1f}C < SM_DRYFAN_DIFF_DEW_C {config.SM_DRYFAN_DIFF_DEW_C:0.1f}C AND filament_dew_C {sensoren.sensor_sht31_filament.measurement_dew_C.value:0.1f}C > SM_DRYFAN_DEW_SET_C {config.SM_DRYFAN_DEW_SET_C:0.1f}C"
                    if (
                        sensoren.sensor_sht31_filament.measurement_dew_C.value
                        > config.SM_DRYFAN_DEW_SET_C
                    ):
                        self._switch(self._state_regenerate, why)
                        return
                    self._switch(
                        self._state_drywait,
                        why.replace(
                            "C > SM_DRYFAN_DEW_SET_C", "C <= SM_DRYFAN_DEW_SET_C"
                        ),
                    )

    # State: DRY WAIT
    def _entry_drywait(self) -> None:
        hardware.PIN_GPIO_FAN_SILICAGEL.off()
        hardware.PIN_GPIO_FAN_AMBIENT.off()
        hardware.heater.set_power(False)
        self._dry_wait_filament_dew_C = (
            sensoren.sensor_sht31_filament.measurement_dew_C.value
        )

        hardware.PIN_GPIO_LED_GREEN.value(1)
        hardware.PIN_GPIO_LED_RED.value(0)
        hardware.PIN_GPIO_LED_WHITE.value(0)

    def _state_drywait(self) -> None:
        if self.forward_to_next_state:
            self._switch(self._state_off, "Forward to next state")
            return

        # diff_dew_C ist positiv wenn der Taupunkt zunimmt
        diff_dew_C = (
            sensoren.sensor_sht31_filament.measurement_dew_C.value
            - self._dry_wait_filament_dew_C
        )
        switch_to_fan_on = diff_dew_C > config.SM_DRYWAIT_DIFF_DEW_C

        if switch_to_fan_on:
            self._switch(
                self._state_dryfan, f"dew filament increased by {diff_dew_C:0.1f}C"
            )


sm = Statemachine()
sensoren.sensor_statemachine.set_sm(sm=sm)


# print(LogfileTags.SENSORS_HEADER)


def main_core2():
    print("filament_dryer started")

    # Wait for main thread to completely load the module
    # import time
    # time.sleep(1)

    # Make sure, 'wlan' and 'mqtt' are instantiated in the thread which will access them
    wlan = utils_wlan.WLAN()
    mqtt = utils_wlan.MQTT(wlan)

    def statechange(old: str, new: str, why: str) -> None:
        mqtt.publish_annotation(
            title=f"Statechange: {old} -> {new}", text=f"Why: {why}"
        )

    sm.statechange_cb = statechange

    def statemachine_cb(msg: str):
        print(f"statemachine_cb: {msg}")
        sm.switch_by_name(msg)

    mqtt.register_callback("statemachine", statemachine_cb)

    logfile.log(LogfileTags.SENSORS_HEADER, sensoren.sensors.get_header())

    while True:
        sensoren.sensors.measure()

        sm.state()
        hardware.heater.set_board_C(board_C=sensoren.sensor_ds18_heater.heater_C)

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


def pressed(duration_ms: int) -> None:
    sm.set_forward_to_next_state()


def long_pressed(timer) -> None:
    # Hard reset micropython
    reset()


utils_button.Button(
    hardware.PIN_GPIO_BUTTON,
    pressed_cb=pressed,
    cb_long_press=long_pressed,
    long_press_ms=2000,
    invers=True,
)


if True:
    # hardware.PIN_GPIO_LED_GREEN.value(0)
    # hardware.PIN_GPIO_LED_RED.value(0)
    # hardware.PIN_GPIO_LED_WHITE.value(0)
    g.stdout = True
    # print(sensors.get_header(stdout_measurements))
    main_core2()
else:
    _thread.start_new_thread(main_core2, ())

# PIN_GPIO_HEATER_A.value(1)
# PIN_GPIO_HEATER_B.value(1)
# PIN_GPIO_FAN_AMBIENT.value(1)
# PIN_GPIO_FAN_SILICAGEL.value(1)


def thread():
    _thread.start_new_thread(main_core2, ())


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


# def df():  # Disk Free
#     print("*** Garbage")
#     print(
#         f"Allocated/Free {gc.mem_alloc()/1000.0:0.3f}/{gc.mem_free()/1000.0:0.3f} kBytes"
#     )
#     gc.collect()
#     print(
#         f"Allocated/Free {gc.mem_alloc()/1000.0:0.3f}/{gc.mem_free()/1000.0:0.3f} kBytes"
#     )

#     print("*** Filesystem")
#     logfile.flush()
#     (
#         f_bsize,
#         f_frsize,
#         f_blocks,
#         f_bfree,
#         f_bavail,
#         f_files,
#         f_ffree,
#         f_favail,
#         f_flag,
#         f_namemax,
#     ) = os.statvfs(DIRECTORY_LOGS)
#     print(f"File system size total:  {f_blocks*f_frsize/1024.0} kBytes")
#     print(f"File system size free:  {f_bavail*f_bsize/1024.0} kBytes")
#     print(f"File system inodes free:  {f_favail}/{f_ffree} inodes")

#     print("*** Logfiles")
#     for name, type, inode, size in os.ilistdir("logs"):
#         print(f"{DIRECTORY_LOGS}/{name}: {size} bytes")


# def rmo():
#     logfile.rm_other_files()


# def format():  # Reformat
#     heater.set_power(False)

#     # https://www.i-programmer.info/programming/hardware/16334-raspberry-pi-pico-file-system-a-sd-card-reader.html?start=1
#     from rp2 import Flash

#     flash = Flash()
#     os.umount("/")
#     os.VfsLfs2.mkfs(flash)
#     os.mount(flash, "/")
#     machine.soft_reset()


# def smp():
#     print(sm.state_name)


# def smx(new_state: str):
#     sm.switch_by_name(new_state)


# def sm0():
#     sm._switch(sm._state_regenerate, "Manual intervention")


# def sm1():
#     sm._switch(sm._state_cooldown, "Manual intervention")


# def sm2():
#     sm._switch(sm._state_drywait, "Manual intervention")


# def sm3():
#     sm._switch(sm._state_dryfan, "Manual intervention")

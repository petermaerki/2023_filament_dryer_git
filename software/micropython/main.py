from machine import Pin, I2C
import time
import os
import gc
import _thread
import neopixel

from utils_constants import DIRECTORY_LOGS
from utils_log import Logfile, LogfileTags
from utils_time import Timebase
from utils_measurement import SensorDS18, SensorFan, SensorHeater, SensorSHT31, Sensors
import utils_measurement

FAST = False
if FAST:
    import config_fast as config
else:
    import config_normal as config


class Globals:
    def __init__(self):
        self.stdout = False
        self.stop_thread = False


g = Globals()

PIN_GPIO_NP_A = Pin("GPIO1", mode=Pin.OUT)
PIN_GPIO_NP_B = Pin("GPIO25", mode=Pin.OUT)
PIN_GPIO_NP_C = Pin("GPIO2", mode=Pin.OUT)
PIN_GPIO_NP_BOARD = Pin("GPIO0", mode=Pin.OUT)

PIN_GPIO_FAN_AMBIENT = Pin("GPIO21", mode=Pin.OUT)
PIN_GPIO_FAN_SILICAGEL = Pin("GPIO9", mode=Pin.OUT)

PIN_T_HEATING_1WIRE = Pin("GPIO15")
PIN_T_AUX_1WIRE = Pin("GPIO14")
PIN_HT_BOARD_SDA = Pin("GPIO26")
PIN_HT_BOARD_SCL = Pin("GPIO27")

PIN_HT_GROVE_SDA = Pin("GPIO12")
PIN_HT_GROVE_SCL = Pin("GPIO13")

i2c_board = I2C(id=1, scl=PIN_HT_BOARD_SCL, sda=PIN_HT_BOARD_SDA, freq=400000)
i2c_ext = I2C(id=0, scl=PIN_HT_GROVE_SCL, sda=PIN_HT_GROVE_SDA, freq=400000)

tb = Timebase(interval_ms=config.MEASURE_INTERVAL_MS)
logfile = Logfile(timebase=tb)
utils_measurement.logfile = logfile


class Config:
    def __init__(self, duration_regenerate_ms: float, duration_dry_ms: float):
        self.duration_regenerate_ms = duration_regenerate_ms
        self.duration_dry_ms = duration_dry_ms


class Heater:
    def __init__(
        self,
    ):
        self._power = 0
        self._board_C = 0.0
        self._neopixels = [
            neopixel.NeoPixel(pin, 10)
            for pin in (PIN_GPIO_NP_A, PIN_GPIO_NP_B, PIN_GPIO_NP_C)
        ]
        self.write_power()

    @property
    def power_controlled(self) -> int:
        if self._board_C > config.HEATER_BOARD_MAX:
            return 0
        return self._power

    def set_power(self, power: int):
        self._power = max(0, min(200, power))

        self.write_power()

    def set_board_C(self, board_C: int):
        self._board_C = board_C

        self.write_power()

    def write_power(self) -> None:
        power = self.power_controlled

        v = (power, power, power)

        for np in self._neopixels:
            for i in range(np.n):
                np[i] = v
            np.write()


heater = Heater()

ds18_board = SensorDS18("heater", PIN_T_HEATING_1WIRE)
sht31_silicagel = SensorSHT31("silicagel", addr=0x44, i2c=i2c_board)
sht31_board = SensorSHT31("board", addr=0x45, i2c=i2c_board)
sht31_ext = SensorSHT31("ext", addr=0x44, i2c=i2c_ext)

sensors = Sensors(
    sensors=[
        SensorHeater("heater", heater),
        SensorFan("silicagel", PIN_GPIO_FAN_SILICAGEL),
        SensorFan("ambient", PIN_GPIO_FAN_AMBIENT),
        sht31_silicagel,
        sht31_board,
        sht31_ext,
        ds18_board,
        SensorDS18("aux", PIN_T_AUX_1WIRE),
    ],
)


class Statemachine:
    PREFIX_STATE = "_state_"
    PREFIX_ENTRY = "_entry_"

    def __init__(self):
        self.state = None
        self.state_name = "none"
        self._start_ms = 0

        self._dryfan_list_dew_C = []
        self._dryfan_next_ms = 0

    def start(self):
        self._switch(self._state_regenerate, "Statemachine initialization")

    @property
    def duration_ms(self) -> int:
        return tb.now_ms - self._start_ms

    def _switch(self, new_state, why: str) -> None:
        assert new_state.__name__.startswith(self.PREFIX_STATE)
        new_state_name = new_state.__name__.replace(self.PREFIX_STATE, "")
        if self.state_name == new_state_name:
            return
        logfile.log(
            LogfileTags.SM_STATE,
            f"'{self.state_name}' -> '{new_state_name}' {why}",
            stdout=True,
        )
        self.state_name = new_state_name
        self.state = new_state
        self._start_ms = tb.now_ms

        new_entry_name = self.PREFIX_ENTRY + new_state_name
        f_entry = getattr(self, new_entry_name)
        f_entry()

    def _entry_regenerate(self) -> None:
        PIN_GPIO_FAN_AMBIENT.off()
        PIN_GPIO_FAN_SILICAGEL.off()
        heater.set_power(255)

    def _state_regenerate(self) -> None:
        diff_dew_C = (
            sht31_silicagel.measurement_dew_C.value - sht31_ext.measurement_dew_C.value
        )
        fan_on = diff_dew_C > config.SM_REGENERATE_DIFF_DEW_C
        PIN_GPIO_FAN_AMBIENT.value(fan_on)

        if fan_on:
            return

        if self.duration_ms > config.DURATION_REGENERATE_MS:
            self._switch(self._state_drywait, "timebox over and fan off")

    def _entry_drywait(self) -> None:
        PIN_GPIO_FAN_SILICAGEL.off()
        PIN_GPIO_FAN_AMBIENT.off()
        heater.set_power(0)

    def _state_drywait(self) -> None:
        diff_dew_C = (
            sht31_board.measurement_dew_C.value
            - sht31_silicagel.measurement_dew_C.value
        )
        fan_on = diff_dew_C > config.SM_DRYWAIT_DIFF_DEW_C

        if fan_on:
            self._switch(
                self._state_dryfan, f"drw difference reached {diff_dew_C:0.1f}C"
            )

    def _entry_dryfan(self) -> None:
        PIN_GPIO_FAN_SILICAGEL.on()
        PIN_GPIO_FAN_AMBIENT.off()
        heater.set_power(0)
        self._dryfan_list_dew_C = []
        self._dryfan_next_ms = tb.now_ms

    def _state_dryfan(self) -> None:
        if tb.now_ms >= self._dryfan_next_ms:
            logfile.log(
                LogfileTags.LOG_INFO,
                f"len={len(self._dryfan_list_dew_C)}, append({sht31_board.measurement_dew_C.value})",
                stdout=True,
            )
            self._dryfan_next_ms += config.SM_DRYFAN_NEXT_MS
            self._dryfan_list_dew_C.append(sht31_board.measurement_dew_C.value)

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
                    why = f"reduction_dew_C {reduction_dew_C:0.1f}C > SM_DRYFAN_DEW_SET_C {config.SM_DRYFAN_DEW_SET_C:0.1f}C"
                    if sht31_board.measurement_dew_C.value > config.SM_DRYFAN_DEW_SET_C:
                        self._switch(self._state_regenerate, why)
                        return
                    self._switch(self._state_drywait, why.replace("C > SM", "C <= SM"))


sm = Statemachine()


def main_core2():
    print("filament_dryer started")
    logfile.log(LogfileTags.SENSORS_HEADER, sensors.header)
    sm.start()

    while True:
        sensors.measure()

        sm.state()
        heater.set_board_C(board_C=ds18_board.board_C)

        # logfile.log(LogfileTags.LOG_DEBUG, f"{tb.sleep_done_ms}, {tb.sleep_done_ms}")
        logfile.log(LogfileTags.SENSORS_VALUES, sensors.values, stdout=g.stdout)

        if g.stop_thread:
            logfile.log(LogfileTags.LOG_INFO, "Stopping", stdout=True)
            logfile.flush()
            return

        tb.sleep()


if False:
    main_core2()
else:
    _thread.start_new_thread(main_core2, ())


def s0():
    g.stdout = False


def s1():
    g.stdout = True
    print(sensors.header)


def fa():
    PIN_GPIO_FAN_AMBIENT.toggle()


def fs():
    PIN_GPIO_FAN_SILICAGEL.toggle()


def hd():
    print(sensors.header)


def h(power: int):
    heater.set_power(power)


def stop():
    g.stop_thread = True


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

    print("*** Logfiles")
    for name, type, inode, size in os.ilistdir("logs"):
        print(f"{DIRECTORY_LOGS}/{name}: {size} bytes")


def rmo():
    logfile.rm_other_files()


def rf():  # Reformat
    heater.set_power(0)

    # https://www.i-programmer.info/programming/hardware/16334-raspberry-pi-pico-file-system-a-sd-card-reader.html?start=1
    from rp2 import Flash

    flash = Flash()
    os.umount("/")
    os.VfsLfs2.mkfs(flash)
    os.mount(flash, "/")
    machine.soft_reset()


def smp():
    print(sm.state_name)


def sm1():
    sm._switch(sm._state_regenerate, "Manual intervention")


def sm2():
    sm._switch(sm._state_drywait, "Manual intervention")


def sm3():
    sm._switch(sm._state_dryfan, "Manual intervention")

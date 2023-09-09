print("main() started")


from machine import Pin, I2C
import time
import os
import _thread
import neopixel

from utils_log import Logfile, LogfileTags
from utils_time import Timebase
from utils_measurement import SensorDS18, SensorFan, SensorHeater, SensorSHT31, Sensors
import utils_measurement


class Globals:
    def __init__(self):
        self.measure_interval_ms = 2000
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

tb = Timebase(interval_ms=g.measure_interval_ms)
logfile = Logfile(timebase=tb)
utils_measurement.logfile = logfile


class Heater:
    def __init__(
        self,
    ):
        self._power = 0
        self._board_C = 0.0
        self._board_max_C = 90.0
        self._neopixels = [
            neopixel.NeoPixel(pin, 10)
            for pin in (PIN_GPIO_NP_A, PIN_GPIO_NP_B, PIN_GPIO_NP_C)
        ]
        self.write_power()

    @property
    def power_controlled(self) -> int:
        if self._board_C > self._board_max_C:
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

sensors = Sensors(
    sensors=[
        SensorHeater("heater", heater),
        SensorFan("silicagel", PIN_GPIO_FAN_SILICAGEL),
        SensorFan("ambient", PIN_GPIO_FAN_AMBIENT),
        SensorSHT31("silicagel", addr=0x44, i2c=i2c_board),
        SensorSHT31("board", addr=0x45, i2c=i2c_board),
        SensorSHT31("ext", addr=0x44, i2c=i2c_ext),
        ds18_board,
        SensorDS18("aux", PIN_T_AUX_1WIRE),
    ],
)


def main_core2():
    try:
        os.mkdir("logs")
    except OSError:
        # The directory might already exit.
        pass

    logfile.log(LogfileTags.SENSORS_HEADER, sensors.header)

    while True:
        sensors.measure()

        heater.set_board_C(ds18_board.board_C)

        logfile.log(LogfileTags.LOG_DEBUG, f"{tb.sleep_done_ms}, {tb.sleep_done_ms}")
        logfile.log(LogfileTags.LOG_DEBUG, sensors.values)
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

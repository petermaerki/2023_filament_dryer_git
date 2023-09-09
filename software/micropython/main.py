print("main() started")


from machine import Pin, I2C
import time
import os
import _thread
import neopixel

from utils_log import Logfile, LogfileTags
from utils_time import Timebase
from utils_measurement import Sensors, SensorSHT31, SensorDS18, SensorFan


class Globals:
    def __init__(self):
        self.measure_interval_ms = 2000
        self.stdout = False


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

sensors = Sensors(
    [
        SensorSHT31("silicagel", addr=0x44, i2c=i2c_board),
        SensorSHT31("board", addr=0x45, i2c=i2c_board),
        SensorSHT31("ext", addr=0x44, i2c=i2c_ext),
        SensorDS18("board", PIN_T_HEATING_1WIRE),
        SensorDS18("aux", PIN_T_AUX_1WIRE),
        SensorFan("ambient", PIN_GPIO_FAN_AMBIENT),
        SensorFan("silicagel", PIN_GPIO_FAN_SILICAGEL),
    ]
)


class Heater:
    def __init__(self):
        self._neopixels = [
            neopixel.NeoPixel(pin, 10)
            for pin in (PIN_GPIO_NP_A, PIN_GPIO_NP_B, PIN_GPIO_NP_C)
        ]

    def power(self, p: int):
        assert 0 <= p < 256
        for np in self._neopixels:
            for i in range(np.n):
                np[i] = (p, p, p)
            np.write()

heater = Heater(1)

if False:
    # for pin in (PIN_GPIO_NP_A, ):
    for pin, n in (
        (PIN_GPIO_NP_BOARD, 2),
        (PIN_GPIO_NP_A, 10),
        (PIN_GPIO_NP_B, 10),
        (PIN_GPIO_NP_C, 10),
    ):
        np = neopixel.NeoPixel(pin, n)
        if True:
            for j in range(n):
                np[j] = (24, 12, 12)
            np.write()


def main_core2():
    try:
        os.mkdir("logs")
    except OSError:
        # The directory might already exit.
        pass

    tb = Timebase(interval_ms=g.measure_interval_ms)
    l = Logfile(timebase=tb)
    l.log(LogfileTags.SENSORS_HEADER, sensors.header)

    while True:
        sensors.measure()

        l.log(LogfileTags.LOG_DEBUG, f"{tb.sleep_done_ms}, {tb.sleep_done_ms}")
        l.log(LogfileTags.LOG_DEBUG, sensors.values)
        l.log(LogfileTags.SENSORS_VALUES, sensors.values, stdout=g.stdout)
        l.flush()

        tb.sleep()


if False:
    main_core2()
else:
    _thread.start_new_thread(main_core2, ())

    if False:
        PIN_GPIO_FAN_AMBIENT.off()
        PIN_GPIO_FAN_SILICAGEL.off()
        while True:
            time.sleep(3.0)
            PIN_GPIO_FAN_AMBIENT.toggle()
            time.sleep(3.0)
            PIN_GPIO_FAN_SILICAGEL.toggle()


# Befehle
def stdout(on):
    g.stdout = on


def f_a():
    PIN_GPIO_FAN_AMBIENT.toggle()


def f_s():
    PIN_GPIO_FAN_SILICAGEL.toggle()


def h(p: int):
    heater.power(p)

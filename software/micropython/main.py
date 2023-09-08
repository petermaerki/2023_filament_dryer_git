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
        self.measure_interval_ms = 1000
        self.flush_file = False


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

sensors = Sensors(
    [
        SensorSHT31(
            "board",
            addr=0x45,
            i2c=I2C(id=1, scl=PIN_HT_BOARD_SCL, sda=PIN_HT_BOARD_SDA, freq=400000),
        ),
        SensorSHT31(
            "ext",
            addr=0x44,
            i2c=I2C(id=0, scl=PIN_HT_GROVE_SCL, sda=PIN_HT_GROVE_SDA, freq=400000),
        ),
        SensorDS18("board", PIN_T_HEATING_1WIRE),
        # SensorDS18("heating", Pin("GPIO8")),
        SensorDS18("aux", PIN_T_AUX_1WIRE),
        SensorFan("ambient", PIN_GPIO_FAN_AMBIENT),
        SensorFan("silicagel", PIN_GPIO_FAN_SILICAGEL),
    ]
)

# PIN_GPIO_NP_A.value(0)
# print(PIN_GPIO_NP_A, PIN_GPIO_NP_A.value())

while False:
    PIN_GPIO_NP_BOARD.toggle()
    print(PIN_GPIO_NP_BOARD, PIN_GPIO_NP_BOARD.value())
    time.sleep_ms(2000)

while False:
    for pin in (PIN_GPIO_NP_BOARD, PIN_GPIO_NP_A, PIN_GPIO_NP_B, PIN_GPIO_NP_C):
        # pin.toggle()
        pin.value(0)
        print(pin, pin.value())
        time.sleep_ms(2000)

if False:
    np = neopixel.NeoPixel(PIN_GPIO_NP_BOARD, 2)
    while True:
        np[0] = (255, 0, 0)  # set to red, full brightness
        np[1] = (0, 128, 0)  # set to green, half brightness
        np.write()
        print(PIN_GPIO_NP_BOARD, PIN_GPIO_NP_BOARD.value())
        time.sleep_ms(200)

if True:
    # for pin in (PIN_GPIO_NP_A, ):
    for pin, n in (
        (PIN_GPIO_NP_BOARD, 2),
        (PIN_GPIO_NP_A, 10),
        (PIN_GPIO_NP_B, 10),
        (PIN_GPIO_NP_C, 10),
    ):
        np = neopixel.NeoPixel(pin, n)
        if False:
            np[0] = (255, 0, 0)  # set to red, full brightness
            np[1] = (0, 128, 0)  # set to green, half brightness
            np[2] = (0, 0, 64)  # set to blue, quarter brightness
            np.write()
            print(pin)
        if True:
            for j in range(n):
                np[j] = (24, 12, 12)
            np.write()
        if False:
            for i in range(4 * n):
                for j in range(n):
                    np[j] = (0, 0, 128)
                if (i // n) % 2 == 0:
                    np[i % n] = (0, 0, 0)
                else:
                    np[n - 1 - (i % n)] = (0, 0, 0)
                np.write()
                time.sleep_ms(60)


def main_core2():
    tb = Timebase(interval_ms=g.measure_interval_ms)

    try:
        os.mkdir("logs")
    except OSError:
        # The directory might already exit.
        pass
    l = Logfile(timebase=tb)
    l.log(LogfileTags.SENSORS_HEADER, sensors.header)

    while True:
        sensors.measure()

        l.log(LogfileTags.LOG_DEBUG, f"{tb.sleep_done_ms}, {tb.sleep_done_ms}")
        l.log(LogfileTags.LOG_DEBUG, sensors.values)
        l.log(LogfileTags.SENSORS_VALUES, sensors.values)
        l.flush()

        tb.sleep()


if False:
    main_core2()
else:
    _thread.start_new_thread(main_core2, ())

    while True:
        PIN_GPIO_FAN_AMBIENT.toggle()
        time.sleep(3.0)
        PIN_GPIO_FAN_SILICAGEL.toggle()
        time.sleep(3.0)

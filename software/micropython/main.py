print("main() started")


from machine import Pin, I2C
import time
import os
import _thread


from utils_log import Logfile, LogfileTags
from utils_time import Timebase
from utils_measurement import Sensors, SensorSHT31, SensorDS18



class Globals:
    def __init__(self):
        self.measure_interval_ms = 1000
        self.flush_file = False


g = Globals()


sensors = Sensors(
    [
        SensorSHT31(
            "board",
            i2c=I2C(id=1, scl=Pin("GPIO11"), sda=Pin("GPIO10"), freq=400000),
        ),
        # SensorSHT31(
        #     "ext",
        #     i2c=I2C(id=0, scl=Pin("GPIO5"), sda=Pin("GPIO4"), freq=400000),
        # ),
        SensorDS18("board", Pin("GPIO0")),
        SensorDS18("heating", Pin("GPIO8")),
        # SensorDS18("ext", Pin("GPIO2")),
    ]
)



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


main_core2()

# _thread.start_new_thread(main_core2, ())

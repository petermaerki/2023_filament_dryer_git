print("main() started")


from machine import Pin, I2C
import time
import os
import _thread

import lib_sht31
from onewire import OneWire
from ds18x20 import DS18X20


class LogfileTags:
    SENSORS_HEADER = "SENSORS_HEADER"
    SENSORS_UNITS = "SENSORS_UNITS"
    SENSORS_VALUES = "SENSORS_VALUES"


class Globals:
    def __init__(self):
        self.measure_interval_ms = 1000
        self.flush_file = False


g = Globals()


class Measurement:
    def __init__(self, sensor: "SensorBase", tag: str, unit: str, format: str):
        self._sensor = sensor
        self._tag = tag
        self._unit = unit
        self._format: str = format
        self.value: float = None

    @property
    def tag(self) -> str:
        return f"{self._sensor.tag}{self._tag}"

    @property
    def value_text(self):
        return self._format.format(value=self.value, unit=self._unit)


class SensorBase:
    def __init__(self, tag: str, measurements: list):
        self.tag = tag
        self._measurements = measurements

    def measure1(self):
        pass

    def measure2(self):
        raise Exception("Please override")


class SensorSHT31(SensorBase):
    def __init__(self, tag: str, i2c: I2C):
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        self.measurement_H = Measurement(self, "_rH", "H", "{value:0.1f}")
        SensorBase.__init__(
            self, tag=tag, measurements=[self.measurement_C, self.measurement_H]
        )
        self._sht31 = lib_sht31.SHT31(i2c, addr=0x44)

    def measure2(self):
        self.measurement_C.value, self.measurement_H.value = self._sht31.get_temp_humi()


class SensorDS18(SensorBase):
    # DS18x: mandatory pause to collect results, datasheet max 750 ms
    MEASURE_MS = const(750)

    def __init__(self, tag: str, pin: Pin):
        self._ds18 = DS18X20(OneWire(pin))
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_C])
        self._sensors = self._ds18.scan()

    def measure1(self):
        self._ds18.convert_temp()

    def measure2(self):
        # time.sleep_ms(
        #     750 + 150
        # )  # mandatory pause to collect results, datasheet max 750 ms
        self.measurement_C.value = self._ds18.read_temp(self._sensors[0])


class Sensors:
    def __init__(self, sensors):
        self._sensors = sensors
        self._measurements = []
        for s in self._sensors:
            for m in s._measurements:
                self._measurements.append(m)

    def measure(self):
        start_ms = time.ticks_ms()
        for s in self._sensors:
            s.measure1()

        duration_ms = time.ticks_diff(time.ticks_ms(), start_ms)
        sleep_ms = SensorDS18.MEASURE_MS - duration_ms
        assert sleep_ms > 0
        time.sleep_ms(sleep_ms)

        for s in self._sensors:
            s.measure2()

    @property
    def header(self) -> str:
        return " ".join([m.tag for m in self._measurements])

    @property
    def values(self) -> str:
        return " ".join([m.value_text for m in self._measurements])


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


class Timebase:
    def __init__(self):
        self.start_ms = time.ticks_ms()
        self.measure_next_ms = 0
        self.sleep_done_ms = 0

    def sleep(self):
        now_ms = time.ticks_diff(time.ticks_ms(), self.start_ms)
        self.measure_next_ms += g.measure_interval_ms
        
        sleep_ms = self.measure_next_ms - now_ms
        if (sleep_ms < 0) or (sleep_ms > g.measure_interval_ms):
            print(f"WARNING: sleep_ms={sleep_ms}")
        if sleep_ms > 0:
            time.sleep_ms(sleep_ms)

        self.sleep_done_ms = time.ticks_diff(time.ticks_ms(), self.start_ms)


def main_core2():
    tb = Timebase()

    try:
        os.mkdir("logs")
    except OSError:
        # The directory might already exit.
        pass
    f = open("logs/logdata.txt", "w")
    f.write(LogfileTags.SENSORS_HEADER)
    f.write(sensors.header)
    f.write("\n")

    while True:
        sensors.measure()

        f.write(LogfileTags.SENSORS_VALUES)
        print(str(tb.sleep_done_ms))
        f.write(str(tb.sleep_done_ms))
        f.write(sensors.values)
        f.write("\n")
        f.flush()

        tb.sleep()


main_core2()

# _thread.start_new_thread(main_core2, ())

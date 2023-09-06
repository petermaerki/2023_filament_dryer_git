import time

import lib_sht31
from onewire import OneWire
from ds18x20 import DS18X20


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
    def __init__(self, tag: str, addr: int, i2c: I2C):
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        self.measurement_H = Measurement(self, "_rH", "H", "{value:0.1f}")
        SensorBase.__init__(
            self, tag=tag, measurements=[self.measurement_C, self.measurement_H]
        )
        self._sht31 = lib_sht31.SHT31(i2c, addr=addr)

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

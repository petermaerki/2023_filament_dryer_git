print("main() started")


from machine import Pin, I2C
import lib_sht31
import time
from onewire import OneWire
from ds18x20 import DS18X20

class LogfileTags:
    SENSORS_HEADER = 'SENSORS_HEADER'
    SENSORS_UNITS = 'SENSORS_UNITS'
    SENSORS_VALUES = 'SENSORS_VALUES'

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

    def measure(self):
        raise Exception("Please override")


class SensorSHT31(SensorBase):
    def __init__(self, tag: str, i2c: I2C):
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        self.measurement_H = Measurement(self, "_rH", "H", "{value:0.1f}")
        SensorBase.__init__(
            self, tag=tag, measurements=[self.measurement_C, self.measurement_H]
        )
        self._sht31 = lib_sht31.SHT31(i2c, addr=0x44)

    def measure(self):
        self.measurement_C.value, self.measurement_H.value = self._sht31.get_temp_humi()


class SensorDS18(SensorBase):
    def __init__(self, tag: str, pin: Pin):
        self._ds18 = DS18X20(OneWire(pin))
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_C])
        self._sensors = self._ds18.scan()

    def measure(self):
        # print(sensors)
        self._ds18.convert_temp()
        time.sleep_ms(
            750 + 150
        )  # mandatory pause to collect results, datasheet max 750 ms
        self.measurement_C.value = self._ds18.read_temp(self._sensors[0])


class Sensors:
    def __init__(self, sensors):
        self._sensors = sensors
        self._measurements = []
        for s in self._sensors:
            for m in s._measurements:
                self._measurements.append(m)

    def measure(self):
        for s in self._sensors:
            s.measure()

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

f = open('logdata.txt', 'w')
f.write(sensors.header)
f.write("\n")
while True:
    sensors.measure()
    f.write(sensors.values)
    f.write("\n")
    f.flush()

    time.sleep(0.5)

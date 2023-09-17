import time

import lib_sht31
import onewire
from ds18x20 import DS18X20

from utils_humidity import rel_to_dpt
from utils_log import Logfile, LogfileTags
from utils_constants import LOGFILE_DELIMITER

logfile = None


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
        if self._sensor._broken:
            return "-"
        try:
            return self._format.format(value=self.value, unit=self._unit)
        except Exception as ex:
            print(f"ERROR: {self.tag}: {ex}")


class SensorBase:
    def __init__(self, tag: str, measurements: list):
        self.tag = tag
        self._measurements = measurements
        self._broken = False

    def measure1(self):
        pass

    def measure2(self):
        pass

    def measure3(self):
        pass

    def io_error(self, ex):
        self._broken = True
        logfile.log(
            LogfileTags.LOG_ERROR, f"{self.__class__.__name__} '{self.tag}': {ex}"
        )


ABSOLUTER_NULLPUNKT_C = -273.15
UMGEBUNGSDRUCK_P = 100000.0


class SensorSHT31(SensorBase):
    def __init__(self, tag: str, addr: int, i2c: I2C):
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        self.measurement_H = Measurement(self, "_rH", "H", "{value:0.1f}")
        self.measurement_dew_C = Measurement(self, "_dew", "C", "{value:0.1f}")
        SensorBase.__init__(
            self,
            tag=tag,
            measurements=[
                self.measurement_C,
                self.measurement_H,
                self.measurement_dew_C,
            ],
        )
        try:
            self._sht31 = lib_sht31.SHT31(i2c, addr=addr)
        except Exception as ex:
            self.io_error(ex=ex)

    def measure2(self):
        C, rH = self._sht31.get_temp_humi()
        self.measurement_C.value = C
        self.measurement_H.value = rH
        dpt_K = rel_to_dpt(T=C - ABSOLUTER_NULLPUNKT_C, P=UMGEBUNGSDRUCK_P, RH=rH)
        self.measurement_dew_C.value = dpt_K + ABSOLUTER_NULLPUNKT_C


class SensorDS18(SensorBase):
    # DS18x: mandatory pause to collect results, datasheet max 750 ms
    MEASURE_MS = const(750 + 150)

    def __init__(self, tag: str, pin: Pin):
        self.measurement_C = Measurement(self, "_C", "C", "{value:0.2f}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_C])

        try:
            self._ds18 = DS18X20(onewire.OneWire(pin))
            self._sensors = self._ds18.scan()
        except Exception as ex:
            self.io_error(ex=ex)

    @property
    def heater_C(self) -> None:
        assert not self._broken
        return self.measurement_C.value

    def measure1(self):
        self._ds18.convert_temp()

    def measure3(self):
        # time.sleep_ms(
        #     750 + 150
        # )  # mandatory pause to collect results, datasheet max 750 ms
        self.measurement_C.value = self._ds18.read_temp(self._sensors[0])


class SensorFan(SensorBase):
    def __init__(self, tag: str, pin: Pin):
        self._pin = pin
        self.measurement_1 = Measurement(self, "_Fan", "Fan", "{value:d}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_1])

    def measure2(self):
        self.measurement_1.value = self._pin.value()


class SensorHeater(SensorBase):
    def __init__(self, tag: str, heater: "Heater"):
        self._heater = heater
        self.measurement_heater = Measurement(self, "_heater", "%", "{value:0.0f}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_heater])

    def measure2(self):
        """0 .. 100%"""
        self.measurement_heater.value = self._heater.power_controlled * 100.0 / 255.0


class Sensors:
    def __init__(self, sensors: list):
        self._sensors = sensors
        self._measurements = []
        for s in self._sensors:
            for m in s._measurements:
                self._measurements.append(m)

    def measure(self):
        start_ms = time.ticks_ms()

        for s in self._sensors:
            if not s._broken:
                try:
                    s.measure1()
                except Exception as ex:
                    s.io_error(ex=ex)
                    continue

        for s in self._sensors:
            if not s._broken:
                try:
                    s.measure2()
                except Exception as ex:
                    s.io_error(ex=ex)
                    continue

        duration_ms = time.ticks_diff(time.ticks_ms(), start_ms)
        sleep_ms = SensorDS18.MEASURE_MS - duration_ms
        if sleep_ms > 0:
            time.sleep_ms(sleep_ms)

        for s in self._sensors:
            if not s._broken:
                try:
                    s.measure3()
                except Exception as ex:
                    s.io_error(ex=ex)
                    continue

    @property
    def header(self) -> str:
        return LOGFILE_DELIMITER.join([m.tag for m in self._measurements])

    @property
    def values(self) -> str:
        return LOGFILE_DELIMITER.join([m.value_text for m in self._measurements])

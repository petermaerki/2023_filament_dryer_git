import time
from machine import Pin, I2C
import lib_sht31
import onewire
from ds18x20 import DS18X20

from utils_humidity import rel_to_dpt, rel_to_abs
from utils_log import LogfileTags
from utils_wdt import wdt
from utils_timebase import tb
from utils_constants import LOGFILE_DELIMITER
from utils_logstdout import logfile

class Measurement:
    def __init__(
        self,
        sensor: "SensorBase",
        tag: str,
        unit: str,
        format: str,
        mqtt=True,
        mqtt_string=False,
    ):
        self._sensor = sensor
        self._tag = tag
        self._unit = unit
        self._format: str = format
        self._mqtt = mqtt
        self._mqtt_string = mqtt_string
        self.value: float = None

    @property
    def mqtt(self) -> bool:
        return self._mqtt and not self._sensor._broken

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

    @property
    def value_mqtt(self):
        assert not self._sensor._broken
        try:
            if self._mqtt_string:
                return f'"{self.value}"'
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
        self.measurement_dew_C = Measurement(self, "_dew_C", "C", "{value:0.1f}")
        self.measurement_abs_g_kg = Measurement(self, "_abs_g_kg", "g_kg", "{value:0.2f}")
        SensorBase.__init__(
            self,
            tag=tag,
            measurements=[
                self.measurement_C,
                self.measurement_H,
                self.measurement_dew_C,
                self.measurement_abs_g_kg,
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
        abs_g_kg = 1000.0 * rel_to_abs(T=C - ABSOLUTER_NULLPUNKT_C, P=UMGEBUNGSDRUCK_P, RH=rH)
        self.measurement_abs_g_kg.value = abs_g_kg

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


class SensorOnOff(SensorBase):
    def __init__(self, tag: str, label: str, pin: Pin, inverse: bool = False):
        self._pin = pin
        self._inverse = inverse
        self.measurement_1 = Measurement(self, label, "OnOff", "{value:d}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_1])

    def measure2(self):
        v = self._pin.value()
        if self._inverse:
            v = not v
        self.measurement_1.value = v


class SensorHeater(SensorBase):
    def __init__(self, tag: str, heater: Heater):
        self._heater = heater
        self.measurement_power = Measurement(self, "_Power", "%", "{value:0.0f}")
        SensorBase.__init__(self, tag=tag, measurements=[self.measurement_power])

    def measure2(self):
        """0 .. 100%"""
        self.measurement_power.value = self._heater.power_controlled * 100.0


class SensorStatemachine(SensorBase):
    def __init__(self):
        self._sm = None
        self.measurement_string = Measurement(self, "", "", "{value}", mqtt_string=True)
        SensorBase.__init__(
            self, tag="statemachine", measurements=[self.measurement_string]
        )

    def set_sm(self, sm):
        self._sm = sm

    def measure2(self):
        assert self._sm is not None
        self.measurement_string.value = self._sm.state_name


class SensorUptime(SensorBase):
    def __init__(self):
        self.measurement = Measurement(self, "_h", "h", "{value:0.3f}")
        SensorBase.__init__(self, tag="uptime", measurements=[self.measurement])

    def measure2(self):
        self.measurement.value = tb.now_ms / 3_600_000.0


class Sensors:
    def __init__(self, sensors: list):
        self._sensors = sensors
        self._measurements = []
        for s in self._sensors:
            for m in s._measurements:
                self._measurements.append(m)

    def measure(self):
        start_ms = time.ticks_ms()

        wdt.feed()

        for s in self._sensors:
            if not s._broken:
                try:
                    s.measure1()
                except Exception as ex:
                    s.io_error(ex=ex)
                    continue

        wdt.feed()

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

        wdt.feed()

        for s in self._sensors:
            if not s._broken:
                try:
                    s.measure3()
                except Exception as ex:
                    s.io_error(ex=ex)
                    continue

    def get_header(self, measurements=None) -> str:
        if measurements is None:
            measurements = self._measurements
        return LOGFILE_DELIMITER.join([m.tag for m in measurements])

    def get_values(self, measurements=None) -> str:
        if measurements is None:
            measurements = self._measurements
        return LOGFILE_DELIMITER.join([m.value_text for m in measurements])

    def get_mqtt_fields(self) -> dict:
        return {m.tag: m.value_mqtt for m in self._measurements if m.mqtt}

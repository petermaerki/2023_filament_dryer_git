from mod_hardware import Hardware, Heater

from utils_measurement import (
    SensorDS18,
    SensorOnOff,
    SensorSHT31,
    SensorHeater,
    Sensors,
    SensorStatemachine,
)


class Sensoren:
    def __init__(self, hardware: Hardware, heater=Heater):
        self.sensor_ds18_heater = SensorDS18(
            "heater_ds18", hardware.PIN_T_HEATING_1WIRE
        )
        self.sensor_sht31_spare = SensorSHT31("spare", addr=0x44, i2c=hardware.i2c0)
        self.sensor_sht31_ambient = SensorSHT31("ambient", addr=0x45, i2c=hardware.i2c0)
        self.sensor_sht31_heater = SensorSHT31("heater", addr=0x44, i2c=hardware.i2c1)
        self.sensor_sht31_filament = SensorSHT31(
            "filament", addr=0x45, i2c=hardware.i2c1
        )
        self.sensor_heater_power = SensorHeater("heater", heater)
        self.sensor_statemachine = SensorStatemachine()
        self.sensors = Sensors(
            sensors=[
                self.sensor_statemachine,
                SensorOnOff("button", "", hardware.PIN_GPIO_BUTTON, inverse=True),
                SensorOnOff("led_green", "", hardware.PIN_GPIO_LED_GREEN),
                SensorOnOff("led_red", "", hardware.PIN_GPIO_LED_RED),
                SensorOnOff("led_white", "", hardware.PIN_GPIO_LED_WHITE),
                self.sensor_heater_power,
                SensorOnOff("filament", "_Fan", hardware.PIN_GPIO_FAN_SILICAGEL),
                SensorOnOff("ambient", "_Fan", hardware.PIN_GPIO_FAN_AMBIENT),
                self.sensor_sht31_spare,
                self.sensor_sht31_ambient,
                self.sensor_sht31_heater,
                self.sensor_sht31_filament,
                self.sensor_ds18_heater,
            ],
        )
        self.stdout_measurements = [
            self.sensor_statemachine.measurement_string,
            self.sensor_heater_power.measurement_power,
            self.sensor_ds18_heater.measurement_C,
            self.sensor_sht31_ambient.measurement_H,  # measurement_C, measurement_H, measurement_dew_C
            self.sensor_sht31_heater.measurement_H,
            self.sensor_sht31_filament.measurement_H,
            self.sensor_sht31_spare.measurement_H,
        ]

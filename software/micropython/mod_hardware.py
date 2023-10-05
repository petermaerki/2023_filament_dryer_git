from machine import Pin, I2C

import config

class Heater:
    def __init__(
        self, hardware: "Hardware"
    ):
        self._power = False
        self._board_C = 0.0
        self._hardware = hardware
        self.write_power()

    @property
    def power_controlled(self) -> bool:
        if self._board_C > config.HEATER_BOARD_MAX:
            return False
        return self._power

    def set_power(self, power: bool):
        self._power = power

        self.write_power()

    def set_board_C(self, board_C: int):
        self._board_C = board_C

        self.write_power()

    def write_power(self) -> None:
        power = self.power_controlled

        self._hardware.PIN_GPIO_HEATER_A.value(power)
        self._hardware.PIN_GPIO_HEATER_B.value(power)


class Hardware:
    def __init__(self):
        self.PIN_GPIO_BUTTON = Pin("GPIO22", mode=Pin.IN, pull=Pin.PULL_UP)
        self.PIN_GPIO_LED_GREEN = Pin("GPIO21", mode=Pin.OUT)
        self.PIN_GPIO_LED_RED = Pin("GPIO20", mode=Pin.OUT)
        self.PIN_GPIO_LED_WHITE = Pin("GPIO19", mode=Pin.OUT)

        self.PIN_GPIO_HEATER_A = Pin("GPIO7", mode=Pin.OUT)
        self.PIN_GPIO_HEATER_B = Pin("GPIO2", mode=Pin.OUT)

        self.PIN_GPIO_FAN_AMBIENT = Pin("GPIO0", mode=Pin.OUT)
        self.PIN_GPIO_FAN_SILICAGEL = Pin("GPIO18", mode=Pin.OUT)

        self.PIN_T_HEATING_1WIRE = Pin("GPIO28")

        self.i2c0 = I2C(id=0, scl=Pin("GPIO17"), sda=Pin("GPIO16"), freq=400000)
        self.i2c1 = I2C(id=1, scl=Pin("GPIO27"), sda=Pin("GPIO26"), freq=400000)
        self.heater = Heater(self)



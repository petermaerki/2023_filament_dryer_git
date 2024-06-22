"""
for debuging: delete file main.py on RP2. Execute main.py with Thonny from PC
for final use: put main.py on RP2
"""
import time
import machine
import micropython

from onewire import OneWire
from ds18x20 import DS18X20

# GPIO0 BOARD
# GPIO8 HEATING

ds_board = DS18X20(OneWire(machine.Pin("GPIO0")))
ds_heating = DS18X20(OneWire(machine.Pin("GPIO8")))
ds_ext = DS18X20(OneWire(machine.Pin("GPIO2")))

while True:
    for name, ds in (('board', ds_board), ('heater', ds_heating), ('ext', ds_ext)):
        # print(name)
        sensors = ds.scan()
        # print(sensors)
        ds.convert_temp()
        time.sleep_ms(
            750 + 150
        )  # mandatory pause to collect results, datasheet max 750 ms
        temperatureC = ds.read_temp(sensors[0])
        print(name, temperatureC, "C")

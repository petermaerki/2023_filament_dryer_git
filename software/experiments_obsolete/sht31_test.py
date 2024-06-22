

# SHT31
# HUMIDITY_SDA: GPIO10, PIN14
# HUMIDITY_SCL: GPIO11, PIN15

# TRASH https://github.com/mcauser/micropython-sht31
# https://www.elektronik-kompendium.de/sites/raspberry-pi/bilder/raspberry-pi-pico-gpio.png
# https://github.com/kfricke/micropython-sht31


from machine import Pin, I2C
import sht31
import time
i2c_board = I2C(id=1, scl=Pin("GPIO11"), sda=Pin("GPIO10"), freq=400000)
i2c_ext = I2C(id=0, scl=Pin("GPIO5"), sda=Pin("GPIO4"), freq=400000)

humi_board = sht31.SHT31(i2c_board, addr=0x44)
humi_ext = sht31.SHT31(i2c_ext, addr=0x44)

while True:
  print(humi_board.get_temp_humi())
  print(humi_ext.get_temp_humi())
  time.sleep(0.5)

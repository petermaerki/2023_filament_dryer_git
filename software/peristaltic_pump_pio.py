# https://how2electronics.com/control-stepper-motor-with-drv8825-raspberry-pi-pico/
from machine import Pin, Timer
import utime
import rp2
from machine import Pin 

led_pin = Pin("GPIO9", Pin.OUT)
step_pin = Pin("GPIO2", Pin.OUT)

out_pin = led_pin

if False:
    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
    def blink():
        # label("loop")
        # set(pins, 1)
        # set(pins, 0)
        # jmp(x_dec, "loop")  # If x is zero, then we'll wrap back to beginning
        # Cycles: 1 + 7 + 32 * (30 + 1) = 1000
        set(pins, 1)
        set(x, 31)                  [6]
        label("delay_high")
        nop()                       [29]
        jmp(x_dec, "delay_high")

        # Cycles: 1 + 7 + 32 * (30 + 1) = 1000
        set(pins, 0)
        set(x, 31)                  [6]
        label("delay_low")
        nop()                       [29]
        jmp(x_dec, "delay_low")

    sm = rp2.StateMachine(0, blink, freq=25000, set_base=out_pin)

    sm.active(1)

print("A")
led_pin.value(1)
utime.sleep(1)
print("B")
led_pin.value(0)
utime.sleep(1)
print("Ok")
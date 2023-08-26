# https://how2electronics.com/control-stepper-motor-with-drv8825-raspberry-pi-pico/
from machine import Pin, Timer
import utime
 
step_pin = Pin("GPIO2")
steps_per_revolution = 200
 
# Initialize timer
tim = Timer()
 
def step(t):
    global step_pin
    step_pin.value(not step_pin.value())
 
def rotate_motor(delay):
    # Set up timer for stepping
    tim.init(freq=1000000//delay, mode=Timer.PERIODIC, callback=step)
 
def loop():
    if True:
        print("Spin motor slowly")
        rotate_motor(2000)
        utime.sleep_ms(steps_per_revolution)
        tim.deinit()  # stop the timer
        utime.sleep(1)
 
        print("Spin motor quickly")
        rotate_motor(1000)
        utime.sleep_ms(steps_per_revolution)
        tim.deinit()  # stop the timer
        utime.sleep(1)
 
if __name__ == '__main__':
    loop()

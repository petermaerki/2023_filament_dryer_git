# https://how2electronics.com/control-stepper-motor-with-drv8825-raspberry-pi-pico/
from machine import Pin, Timer
import utime
import rp2
from machine import Pin 

# led_pin = Pin("GPIO9", Pin.OUT) # FILAMENT DRYER
led_pin = Pin(25, Pin.OUT) # PICO
# step_pin = Pin("GPIO2", Pin.OUT)

out_pin = led_pin

class DRV8825:
    """
        This statemachine sends 'count' pulses.
        Pulse length is 'duration_us'.
        The statemachine runs at 10MHz
        The pulse takes 10 PIO-instructions
        Therefore 'duration_us' is in micorsecondes (10MHz/10)
    """
    def __init__(self):
        @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
        def pulses():
            # x=pulses: how many pulses to send
            pull()
            mov(x, osr)
            
            # y=duration_us: duration of one period
            # Store it in 'isr'. Later, we will assign it to y
            pull()
            mov(isr, osr)

            # Outer loop: pulses
            label("pulses_loop")

            # Positive pulse: 5 instructions
            mov(y, isr)
            set(pins, 1)
            label("pulse_positive")
            jmp(y_dec, "pulse_positive") [4]
            
            # Negative pulse: 5 instructions
            mov(y, isr)
            set(pins, 0)
            label("pulse_negative")
            jmp(y_dec, "pulse_negative") [4]
            
            # Outer loop: pulses
            jmp(x_dec, "pulses_loop")
            
            # Done. This will unblock 'sm.get()'
            push(noblock)


        # state machine 0, running at 10MHz
        self.sm = rp2.StateMachine(0, pulses, freq=10_000_000, set_base=out_pin)
        
    def send_pulses(self, pulses:int, duration_us = 1_000_000):
        # Empty fifo
        while self.sm.rx_fifo() > 0:
            self.sm.pull()
        self.sm.active(1)
        self.sm.put(pulses-1)
        self.sm.put(duration_us)
        
    def wait(self, blocking=True) -> bool:
        """
        If blocking is True:
           return True
        If blocking is False:
           return False # If still in progress
        return True # If done
        """
        if not blocking:
            if self.sm.rx_fifo() == 0:
                return False
        self.sm.get()
        return True


x = DRV8825()
x.send_pulses(3)
print("sm.get() before")
x.wait()
print("sm.get() after")



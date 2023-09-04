from machine import Pin,
import rp2

class DRV8825:
    """
        https://how2electronics.com/control-stepper-motor-with-drv8825-raspberry-pi-pico/
        
        This statemachine sends 'count' pulses.
        Pulse length is 'pulse_length_us'.
        The statemachine runs at 10MHz
        The pulse takes 10 PIO-instructions
        Therefore 'pulse_length_us' is in micorsecondes (10MHz/10)
    """
    def __init__(self, id: int, pin: Pin):
        assert 0 <= id < 8

        @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
        def pulses():
            # x=pulses: how many pulses to send
            pull()
            mov(x, osr)
            
            # y=pulse_length_us: duration of one period
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
        self.sm = rp2.StateMachine(id, pulses, freq=10_000_000, set_base=pin)
        
    def send_pulses(self, pulses:int, pulse_length_us = 1_000_000):
        # Empty fifo
        while self.sm.rx_fifo() > 0:
            self.sm.pull()
        self.sm.active(1)
        self.sm.put(pulses-1)
        self.sm.put(pulse_length_us)
        
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

def main():
    d = DRV8825(id=0, pin=Pin(25, Pin.OUT))
    d.send_pulses(3)
    print("wait() before")
    d.wait()
    print("wait() after")

if __name__ == "__main__":
    main()



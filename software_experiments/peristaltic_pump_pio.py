# https://how2electronics.com/control-stepper-motor-with-drv8825-raspberry-pi-pico/
from machine import Pin, Timer
import utime
import rp2
from machine import Pin 

led_pin = Pin("GPIO9", Pin.OUT)
led_pico_pin = Pin(25, Pin.OUT)
step_pin = Pin("GPIO2", Pin.OUT)

out_pin = led_pico_pin

if True:
    # https://www.digikey.at/en/maker/projects/raspberry-pi-pico-and-rp2040-micropython-part-3-pio/3079f9f9522743d09bb65997642e0831

    # Blink state machine program. Blinks LED at 10 Hz (with freq=2000)
    # 2000 Hz / (20 cycles per instruction * 10 instructions) = 10 Hz
    # Single pin (base pin) starts at output and logic low
    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
    def blink():
        pull()
        mov(x, osr)
        # wrap_target()
        label("loop")
        set(pins, 1) [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        set(pins, 0) [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        jmp(x_dec, "loop")
        irq(rel(0))
        # wrap()

    # Init state machine with "blink" program
    # (state machine 0, running at 2kHz, base pin is GP25 (LED))
    sm = rp2.StateMachine(0, blink, freq=2000, set_base=out_pin)
    
    def done(sm):
        print("Done")
    sm.irq(done)

    # Continually start and stop state machine
    print("Starting state machine...")
    sm.active(1)
    while True:
        utime.sleep(5)
        print("put")
        times = 0
        sm.put(times)

if False:
    # https://www.digikey.at/en/maker/projects/raspberry-pi-pico-and-rp2040-micropython-part-3-pio/3079f9f9522743d09bb65997642e0831

    # Blink state machine program. Blinks LED at 10 Hz (with freq=2000)
    # 2000 Hz / (20 cycles per instruction * 10 instructions) = 10 Hz
    # Single pin (base pin) starts at output and logic low
    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
    def blink():
        pull()
        mov(x, osr)
        # wrap_target()
        label("loop")
        set(pins, 1) [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        set(pins, 0) [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        jmp(x_dec, "loop")
        irq(rel(0))
        # wrap()

    # Init state machine with "blink" program
    # (state machine 0, running at 2kHz, base pin is GP25 (LED))
    sm = rp2.StateMachine(0, blink, freq=2000, set_base=out_pin)
    
    def done(sm):
        print("Done")
    sm.irq(done)

    # Continually start and stop state machine
    print("Starting state machine...")
    sm.active(1)
    while True:
        print("A")
        sm.put(10)
        utime.sleep(5)
        print("B")
    
if False:
    # https://www.digikey.at/en/maker/projects/raspberry-pi-pico-and-rp2040-micropython-part-3-pio/3079f9f9522743d09bb65997642e0831
    # Blink state machine program. Blinks LED at 10 Hz (with freq=2000)
    # 2000 Hz / (20 cycles per instruction * 10 instructions) = 10 Hz
    # Single pin (base pin) starts at output and logic low
    @rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
    def blink():
        wrap_target()
        set(pins, 1) [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        set(pins, 0) [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        nop()        [19]
        wrap()

    # Init state machine with "blink" program
    # (state machine 0, running at 2kHz, base pin is GP25 (LED))
    sm = rp2.StateMachine(0, blink, freq=2000, set_base=out_pin)

    # Continually start and stop state machine
    while True:
        print("Starting state machine...")
        sm.active(1)
        utime.sleep(1)
        print("Stopping state machine...")
        sm.active(0)
        utime.sleep(1)

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

    # Create and start a StateMachine with blink_1hz, outputting on Pin(25)
    sm = rp2.StateMachine(0, blink, freq=2000, set_base=out_pin)

    sm.active(1)

if False:
    print("A")
    out_pin.value(1)
    utime.sleep(1)
    print("B")
    out_pin.value(0)
    utime.sleep(1)
    print("Ok")

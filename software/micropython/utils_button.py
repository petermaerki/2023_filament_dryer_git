from machine import Pin, Timer
import micropython
import time


class Button:
    """
    This button is debounced.
    'pressed_cb(duration_ms: int)' will be called whenever the button is released.
    'cb_long_press()' will be called when the button was pressed longer than 'long_press_ms'.
    """

    def __init__(
        self, pin: Pin, pressed_cb, cb_long_press, long_press_ms: int, invers=False
    ):
        self._inverse = invers
        self._pressed_cb = pressed_cb
        self._long_press_cb = cb_long_press
        self._long_press_ms = long_press_ms
        pin.irq(self._irq)
        self._start_ms = time.ticks_ms()
        self._long_press_timer = Timer()

    def _release_timer(self):
        if self._long_press_timer is None:
            return
        self._long_press_timer.deinit()

    def _irq(self, p):
        pressed = p.value() != self._inverse
        duration_ms = time.ticks_diff(time.ticks_ms(), self._start_ms)
        if duration_ms < 20:
            # Bounce
            return
        if pressed == 1:
            self._start_ms = time.ticks_ms()
            self._long_press_timer.init(
                period=self._long_press_ms,
                mode=Timer.ONE_SHOT,
                callback=self._long_press_cb,
            )
            return

        self._long_press_timer.deinit()
        micropython.schedule(self._pressed_cb, duration_ms)

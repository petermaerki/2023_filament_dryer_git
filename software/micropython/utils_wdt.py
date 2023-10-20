"""
https://github.com/nanophysics/pico_nano_monitor/blob/main/utils.py
"""

import machine
import time

# The maximum value for timeout is 8388 ms.
WDT_TIMEOUT_MAX_MS = const(8388)
WDT_SLEEP_MS = const(3500)
WDT_WARNING_MS = const(4000)


class Wdt:
    def __init__(self):
        self._wdt = None
        self._monitor_last_wdt_ms: int = time.ticks_ms()
        self._timeout_ms = WDT_TIMEOUT_MAX_MS
        self._timer = machine.Timer(-1)
        self._list_slow_wdt = []
        self.is_enabled = False

    def enable(self) -> None:
        assert self._wdt is None
        self.is_enabled = True
        self._wdt_start()

    def create_slow_wdt(self, expiration_ms: int) -> "SlowWdt":
        slow_wdt = SlowWdt(expiration_ms)
        self._list_slow_wdt.append(slow_wdt)
        return slow_wdt

    def _wdt_start(self):
        if self.is_enabled:
            self._wdt = machine.WDT(timeout=WDT_TIMEOUT_MAX_MS)
            self._monitor_last_wdt_ms = time.ticks_ms()

    def _wdt_stop(self):
        machine.mem32[0x40058000] = machine.mem32[0x40058000] & ~(1 << 30)
        self._wdt = None

    def _use_timer(self, duration_ms: int):
        if not self.is_enabled:
            return
        # https://github.com/micropython/micropython/issues/8600
        msg = f"TimerWdt reset after {duration_ms}ms"

        def reset(k):
            print(msg)
            machine.reset()

        # Selfmade WDT with no time limit.
        self._timer.init(period=duration_ms, mode=self._timer.ONE_SHOT, callback=reset)
        # board.set_led(value=True, colour=_WHITE) # This way we can find out if pico freezes while WDT halted
        # log.log(f"Wdt is halted temporary", level=TRACE)
        self._wdt_stop()

    def _use_wdt(self):
        if not self.is_enabled:
            return
        self._timer.deinit()
        self._wdt_start()
        # board.set_led(value=False, colour=_WHITE)

    def feed(self):
        time_since_last_feed = time.ticks_diff(
            time.ticks_ms(), self._monitor_last_wdt_ms
        )
        self._monitor_last_wdt_ms = time.ticks_ms()
        if time_since_last_feed > WDT_WARNING_MS:
            # log.log(msg, level=INFO)
            print(f"wdt.feed(), {time_since_last_feed:d} ms elapsed, timeout {self._timeout_ms:d} ms")
        for slow_wdt in self._list_slow_wdt:
            slow_wdt.feed()
        if not self.is_enabled:
            return
        self._wdt.feed()


class SlowWdt:
    def __init__(self, expiration_ms: int):
        self._start_ms: int = None
        self._expiration_ms = expiration_ms

        def __enter__(self):
            self._expiration_ms = expiration_ms
            self._start_ms = time.now()

        def __exit__(self, *exc):
            self._start_ms = None

    def feed(self):
        duration_ms = time.ticks_diff(time.ticks_ms(), self._start_ms)
        if duration_ms > self._expiration_ms:
            print(f"SlowWdt() reset after {duration_ms}ms")
            # Give time to flush print buffer
            time.sleep(0.1)
            machine.reset()


wdt = Wdt()


class TimerWdt:
    def __init__(self, duration_ms=20000):
        self._start_ms = time.ticks_ms()
        self._duration_ms = duration_ms

    def __enter__(self):
        wdt._use_timer(self._duration_ms)
        return self

    def __exit__(self, *exc):
        wdt._use_wdt()
        duration_ms = time.ticks_diff(time.ticks_ms(), self._start_ms)
        print(f"TimerWdt returned after {duration_ms}ms of {self._duration_ms}ms.")

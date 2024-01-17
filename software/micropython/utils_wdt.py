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
        self.is_enabled = False

    def enable(self) -> None:
        assert self._wdt is None
        self._wdt = machine.WDT(timeout=WDT_TIMEOUT_MAX_MS)

    def disable(self) -> None:
        # Stop/disable the RP2040 watchdog timer
        # 0x40058000 = WATCHDOG_CTRL register, bit 30 is the ENABLE bit
        machine.mem32[0x40058000] = machine.mem32[0x40058000] & ~(1 << 30)

    def feed(self):
        time_since_last_feed = time.ticks_diff(
            time.ticks_ms(), self._monitor_last_wdt_ms
        )
        self._monitor_last_wdt_ms = time.ticks_ms()
        if time_since_last_feed > WDT_WARNING_MS:
            # log.log(msg, level=INFO)
            print(
                f"WARNING: wdt.feed(): {time_since_last_feed:d} ms elapsed, timeout {WDT_TIMEOUT_MAX_MS} ms"
            )
        if self._wdt is not None:
            self._wdt.feed()


wdt = Wdt()

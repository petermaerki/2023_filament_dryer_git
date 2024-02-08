import time

import config
from utils_wdt import wdt, WDT_SLEEP_MS


class Timebase:
    def __init__(self, interval_ms: int):
        self._interval_ms = interval_ms
        self.start_ms = time.ticks_ms()
        self.measure_next_ms = time.ticks_add(time.ticks_ms(), self._interval_ms)
        self.sleep_done_ms = 0

    @property
    def now_ms(self) -> int:
        return time.ticks_diff(time.ticks_ms(), self.start_ms)

    def sleep(self):
        self.measure_next_ms = time.ticks_add(self.measure_next_ms, self._interval_ms)

        while True:
            sleep_ms = time.ticks_diff(self.measure_next_ms, time.ticks_ms())
            if sleep_ms < 0:
                break
            if sleep_ms > WDT_SLEEP_MS:
                # Be aware of the watchdog and do not sleep to long
                sleep_ms = WDT_SLEEP_MS
            # if (sleep_ms < 0) or (sleep_ms > self.interval_ms):
            #     print(f"WARNING: sleep_ms={sleep_ms}")
            wdt.feed()
            time.sleep_ms(sleep_ms)

        self.sleep_done_ms = self.now_ms
        wdt.feed()


tb = Timebase(interval_ms=config.MEASURE_INTERVAL_MS)

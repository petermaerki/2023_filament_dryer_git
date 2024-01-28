import time

import config
from utils_wdt import wdt, WDT_SLEEP_MS


class Timebase:
    def __init__(self, interval_ms: int):
        self.interval_ms = interval_ms
        self.start_ms = time.ticks_ms()
        self.measure_next_ms = 0
        self.sleep_done_ms = 0

    @property
    def now_ms(self) -> int:
        return time.ticks_diff(time.ticks_ms(), self.start_ms)

    def sleep(self):
        self.measure_next_ms += self.interval_ms

        while True:
            sleep_ms = self.measure_next_ms - self.now_ms
            if sleep_ms < 0:
                break
            # if (sleep_ms < 0) or (sleep_ms > self.interval_ms):
            #     print(f"WARNING: sleep_ms={sleep_ms}")
            wdt.feed()
            # Be aware of the watchdog and do not sleep to long
            time.sleep_ms(min(sleep_ms, WDT_SLEEP_MS))

        self.sleep_done_ms = self.now_ms
        wdt.feed()


tb = Timebase(interval_ms=config.MEASURE_INTERVAL_MS)

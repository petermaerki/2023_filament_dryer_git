import time

import config

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

        sleep_ms = self.measure_next_ms - self.now_ms
        if (sleep_ms < 0) or (sleep_ms > self.interval_ms):
            print(f"WARNING: sleep_ms={sleep_ms}")
        if sleep_ms > 0:
            time.sleep_ms(sleep_ms)

        self.sleep_done_ms = time.ticks_diff(time.ticks_ms(), self.start_ms)

tb = Timebase(interval_ms=config.MEASURE_INTERVAL_MS)

import machine
import time
import _thread


class SlowWdt:
    def __init__(self, expiration_ms: int):
        self.lock = _thread.allocate_lock()
        self._start_ms: int = None
        self._expiration_ms = expiration_ms

        def __enter__(self):
            with self.lock:
                self._expiration_ms = expiration_ms
                self._start_ms = time.now()

        def __exit__(self, *exc):
            with self.lock:
                self._start_ms = None

    def feed(self):
        with self.lock:
            duration_ms = time.ticks_diff(time.ticks_ms(), self._start_ms)
            if duration_ms > self._expiration_ms:
                print(f"SlowWdt() reset after {duration_ms}ms")
                # Give time to flush print buffer
                time.sleep(0.1)
                machine.reset()

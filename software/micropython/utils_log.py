import _thread


class LogfileTags:
    SENSORS_HEADER = "SENSORS_HEADER"
    SENSORS_UNITS = "SENSORS_UNITS"
    SENSORS_VALUES = "SENSORS_VALUES"
    LOG_ERROR = "LOG_ERROR"
    LOG_WARNING = "LOG_WARNING"
    LOG_INFO = "LOG_INFO"
    LOG_DEBUG = "LOG_DEBUG"


class Logfile:
    def __init__(self, timebase: "Timebase"):
        self.timebase = timebase
        self.f = open("logs/logdata.txt", "w")
        self.lock = _thread.allocate_lock()

    def log(self, tag: str, line: str):
        with self.lock:
            self.f.write(str(self.timebase.now_ms))
            self.f.write(" ")
            self.f.write(tag)
            self.f.write(" ")
            self.f.write(line)
            self.f.write("\n")

    def flush(self):
        self.f.flush()

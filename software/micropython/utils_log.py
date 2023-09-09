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

    def log(self, tag: str, line: str, stdout: bool = False):
        with self.lock:
            self.f.write(str(self.timebase.now_ms))
            self.f.write("\t")
            self.f.write(tag)
            self.f.write("\t")
            self.f.write(line)
            self.f.write("\n")

            write_to_stdout = stdout
            if tag is LogfileTags.LOG_DEBUG:
                write_to_stdout = False
            elif tag is LogfileTags.LOG_ERROR:
                write_to_stdout = True
            if write_to_stdout:
                print("\t".join(str(self.timebase.now_ms), tag, line))

    def flush(self):
        self.f.flush()

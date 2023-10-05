from utils_log import LogfileTags
from utils_constants import DIRECTORY_LOGS, LOGFILE_DELIMITER

class LogStdout:
    def __init__(self, timebase: "Timebase"):
        self.timebase = timebase

    def log(self, tag: str, line: str, stdout: bool = False):
        full_line = LOGFILE_DELIMITER.join(
            (
                str(self.timebase.now_ms),
                tag,
                line,
            )
        )

        def write_to_stdout():
            "Return True if we have to write to stdout"
            if tag is LogfileTags.LOG_DEBUG:
                return False
            if tag is LogfileTags.LOG_ERROR:
                return True
            return stdout

        if write_to_stdout():
            print(full_line)

    def flush(self):
        pass

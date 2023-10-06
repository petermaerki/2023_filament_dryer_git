from utils_log import LogfileTags
from utils_constants import LOGFILE_DELIMITER
from utils_timebase import tb

class LogStdout:
    def log(self, tag: str, line: str, stdout: bool = False):
        full_line = LOGFILE_DELIMITER.join(
            (
                str(tb.now_ms),
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

logfile = LogStdout(timebase=tb)

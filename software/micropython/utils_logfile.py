import os
import _thread

from utils_constants import DIRECTORY_LOGS, LOGFILE_DELIMITER

from utils_log import LogfileTags
from utils_timebase import tb

class Logfile:
    def __init__(self):
        self.filename: str = None
        try:
            os.mkdir(f"{DIRECTORY_LOGS}")
        except OSError:
            # The directory might already exit.
            pass
        files = os.listdir(DIRECTORY_LOGS)
        for i in range(1000):
            filename = f"logdata_{i+10}.txt"
            if not filename in files:
                self.filename = filename
                self.f = open(f"{DIRECTORY_LOGS}/{filename}", "w")
                break
        else:
            raise Exception("Failed to create file!")
        self.lock = _thread.allocate_lock()

    def rm_other_files(self):
        for filename in os.listdir(DIRECTORY_LOGS):
            if filename != self.filename:
                filename_full = f"{DIRECTORY_LOGS}/{filename}"
                print("rm", filename_full)
                os.unlink(filename_full)

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

        with self.lock:
            self.f.write(full_line)
            self.f.write("\n")
            self.f.flush()

    def flush(self):
        with self.lock:
            self.f.flush()

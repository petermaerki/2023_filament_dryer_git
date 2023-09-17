import csv
from dataclasses import dataclass
from datetime import datetime
import re
import pathlib
from typing import List, Tuple
import matplotlib.pyplot as plt

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


def normalize_label(label: str) -> str:
    # Driver, location, measurement unit
    dict_rep = {
        "heater_heater": "heater-Heater-1",
        "silicagel_Fan": "filament-Fan-1",
        "ambient_Fan": "ambient-Fan-1",
        "silicagel_C": "silicagel-temperature-C",  # silicagel-temp-C
        "silicagel_rH": "silicagel-humidity-rH",
        "silicagel_dew": "silicagel-dew-C",  # silicagel-dew-C
        "board_C": "filament-temperature-C",
        "board_rH": "filament-humidity-rH",
        "board_dew": "filament-dew-C",
        "ext_C": "ambient-temperature-C",
        "ext_rH": "ambient-humidity-rH",
        "ext_dew": "ambient-dew-C",
        "heater_C": "heater-temperature-C",
        "aux_C": "aux-temperature-C",
    }
    return dict_rep[label]


LABEL_LOCATIONS = {"heater", "filament", "silicagel", "ambient", "aux"}
LABEL_UNITS = {"1", "C", "rH"}
LABEL_MEASUREMENTS = {"Heater", "Fan", "temperature", "humidity", "dew"}
# Example: silicagel-temperature-C
RE_LABEL = re.compile(r"^(?P<location>\w+)-(?P<measurement>\w+)-(?P<unit>\w+)$")


@dataclass
class Label:
    location: str
    measurement: str
    unit: str

    @staticmethod
    def parse(label: str) -> "Label":
        m = RE_LABEL.match(label)
        label = Label(
            location=m.group("location"),
            measurement=m.group("measurement"),
            unit=m.group("unit"),
        )
        assert label.location in LABEL_LOCATIONS
        assert label.measurement in LABEL_MEASUREMENTS
        return label.unit in LABEL_UNITS


COL_TIME_MS = "time_ms"
COL_SENSORS_HEADERS = "SENSORS_HEADER"


class LogReader:
    def __init__(self, filename: pathlib.Path):
        with open(filename, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter="\t", quotechar="|")
            header = next(reader)
            self._rows = list(reader)

            assert header[1] == COL_SENSORS_HEADERS

        skip_columns = 2
        self._dict_header = {
            normalize_label(label): i + skip_columns
            for i, label in enumerate(header[skip_columns:])
        }
        # Test if label syntax is correct
        for label in self._dict_header:
            Label.parse(label)
        self._dict_header[COL_TIME_MS] = 0
        self._dict_header[COL_SENSORS_HEADERS] = 1

        idx = self.get_col_idx(COL_SENSORS_HEADERS)
        self._rows_filtered = [
            list_row for list_row in self._rows if list_row[idx] == "SENSORS_VALUES"
        ]

        self.x_h = [time_ms / 3_600_000.0 for time_ms in self.get_col_int(COL_TIME_MS)]

    def get_col_idx(self, col: str) -> int:
        return self._dict_header[col]

    def get_col_str(self, col: str) -> List[str]:
        idx = self.get_col_idx(col)
        return [list_row[idx] for list_row in self._rows_filtered]

    def get_col_int(self, col: str) -> List[int]:
        return [int(v) for v in self.get_col_str(col)]

    def get_col_float(self, col: str) -> List[float]:
        return [float(v) for v in self.get_col_str(col)]


def create_diagram(filename: pathlib.Path):
    lr = LogReader(filename)

    # One diagram, one y axis
    fig, ax_temperature = plt.subplots()
    ax_power = ax_temperature

    def get_color(label: str) -> str:
        # https://matplotlib.org/stable/gallery/color/named_colors.html
        if label.startswith("filament"):
            return "gold"
        if label.startswith("ambient"):
            return "lime"
        if label.startswith("silicagel"):
            return "blue"
        if label.startswith("heater"):
            return "red"
        if label.startswith("aux"):
            return "black"
        return "black"

    def get_line_width_and_style(label: str) -> Tuple[float, int, str]:
        if label.endswith("-humidity-rH"):
            return 0.95, 1, "dotted"
        if label.endswith("-temperature-C"):
            return 0.95, 1, "solid"
        if label.endswith("-dew-C"):
            return 0.5, 3, "solid"
        if label.endswith("-Fan") or label.endswith("-Heater"):
            return 0.95, 1, "solid"
        return 0.95, 5, "dotted"

    def add_top(label: str):
        alpha, linewidth, linestyle = get_line_width_and_style(label)
        ax_temperature.plot(
            lr.x_h,
            lr.get_col_float(label),
            linestyle=linestyle,
            linewidth=linewidth,
            color=get_color(label),
            alpha=alpha,
            label=label,
        )

    def reset_svg_date(filename: pathlib.Path) -> None:
        # Example: <dc:date>2023-09-14T07:03:29.061481</dc:date>
        tag_begin = "<dc:date>"
        tag_end = "</dc:date>"
        svg = filename.read_text()
        pos1 = svg.find(tag_begin)
        if pos1 < 0:
            return
        pos2 = svg.find(tag_end, pos1)
        if pos2 < 0:
            return
        filename.write_text(svg[:pos1] + svg[pos2 + len(tag_end) :])

    def add_power(label: str, offset=0.0, scale=1.0):
        # linewidth, linestyle = get_line_width_and_style(label)
        ax_power.plot(
            lr.x_h,
            [v * scale + offset for v in lr.get_col_float(label)],
            linestyle="solid",
            linewidth=1,
            color=get_color(label),
            alpha=0.95,
            label=label,
        )

    # Add data
    power_offset = 110.0
    power_size = 3.0
    power_increment = 5.0
    add_power("ambient-Fan-1", offset=power_offset, scale=power_size)
    power_offset += power_increment
    add_power("filament-Fan-1", offset=power_offset, scale=power_size)
    power_offset += power_increment
    add_power("heater-Heater-1", offset=power_offset, scale=power_size / 127.0)

    add_top("silicagel-temperature-C")
    add_top("silicagel-humidity-rH")
    add_top("silicagel-dew-C")
    add_top("filament-temperature-C")
    add_top("filament-humidity-rH")
    add_top("filament-dew-C")
    add_top("ambient-temperature-C")
    add_top("ambient-humidity-rH")
    add_top("ambient-dew-C")
    add_top("heater-temperature-C")
    add_top("aux-temperature-C")

    # Plot
    ax_temperature.set(xlabel="time (h)", ylabel="Temperature C / rH")
    ax_temperature.grid()
    ax_temperature.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")
    plt.tight_layout()

    if False:
        plt.show()
        raise Exception("Done")
    else:
        # my_dpi = 600
        # my_dpi = fig.dpi
        # # my_dpi = 'figure'
        # fig.set_dpi(my_dpi)
        # fig.set_figheight(4000 / my_dpi)
        # fig.set_figwidth(7000 / my_dpi)

        filename_plt = filename.with_suffix(".svg")

        plt.savefig(
            filename_plt,
            # transparent=True,
            # dpi=my_dpi,
            # https://github.com/matplotlib/matplotlib/blob/4723dabd7885080a326e8ed65a15ce49ab5d4d31/lib/matplotlib/backends/backend_svg.py#L325-L340
            #  metadata={'Date': datetime(year=2000, month=1, day=1)},
            #  metadata={'Date': '2000-01-01'},
        )
        reset_svg_date(filename=filename_plt)

    plt.close()


def main():
    DIRECTORY_EXPERIMENTS = (
        DIRECTORY_OF_THIS_FILE.parent / "dryer_experiments" / "2023-09-11_trials"
    )
    for filename in sorted(DIRECTORY_EXPERIMENTS.glob("*.txt"), reverse=True):
        print(filename)
        create_diagram(filename)
        # return


if __name__ == "__main__":
    main()

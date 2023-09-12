import csv
from dataclasses import dataclass
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

    fig, axs = plt.subplots(2)
    # fig.suptitle("Vertically stacked subplots")

    ax_top, ax_power = axs

    # fig, axs = plt.subplots(2)
    # ax2 = ax.twinx()

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

    def get_line_width_and_style(label: str) -> Tuple[int, str]:
        if label.endswith("-rH"):
            return 1, "dotted"
        if label.endswith("-C"):
            return 1, "solid"
        if label.endswith("-dew"):
            return 2, "solid"
        if label.endswith("-Fan") or label.endswith("-Heater"):
            return 1, "solid"
        return 5, "dotted"

    def add_top(label: str):
        linewidth, linestyle = get_line_width_and_style(label)
        ax_top.plot(
            lr.x_h,
            lr.get_col_float(label),
            linestyle=linestyle,
            linewidth=linewidth,
            color=get_color(label),
            alpha=0.95,
            label=label,
        )

    def add_power(label: str, factor: float = 1.0):
        # linewidth, linestyle = get_line_width_and_style(label)
        ax_power.plot(
            lr.x_h,
            [v * factor for v in lr.get_col_float(label)],
            linestyle="solid",
            linewidth=1,
            color=get_color(label),
            alpha=0.95,
            label=label,
        )

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
    add_power("ambient-Fan-1")
    add_power("filament-Fan-1")
    add_power("heater-Heater-1", factor=1.0 / 127.0)

    ax_top.set(xlabel="time (h)", ylabel="Temperature C / rH")

    ax_top.grid()
    ax_power.set(ylabel="Power")
    # ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.2e"))
    ax_power.ticklabel_format(useOffset=False)

    ax_top.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")
    ax_power.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")
    plt.tight_layout()

    # plt.savefig(
    #     "C:/data/peters_daten\haus_13_zelglistrasse_49/heizung/heizung_peter_schaer_siedlung/heizung_puenterswis_simulation_git/pictures/energiereserve_"
    #     + self.speicher.label
    #     + ".png", **SAVEFIG_KWARGS
    # )

    if True:
        my_dpi = 600
        fig.set_dpi(my_dpi)
        fig.set_figheight(4000 / my_dpi)
        fig.set_figwidth(7000 / my_dpi)

        plt.savefig(
            filename.with_suffix(".svg"),
            # transparent=True,
            dpi=my_dpi,
        )

    if False:
        plt.show()

    plt.close()


if __name__ == "__main__":
    DIRECTORY_EXPERIMENTS = (
        DIRECTORY_OF_THIS_FILE.parent / "dryer_experiments" / "2023-09-11_trials"
    )
    if True:
        for filename in DIRECTORY_EXPERIMENTS.glob("*.txt"):
            print(filename)
            create_diagram(filename)
    else:
        create_diagram(DIRECTORY_EXPERIMENTS / "2023-09-11b_logdata.txt")

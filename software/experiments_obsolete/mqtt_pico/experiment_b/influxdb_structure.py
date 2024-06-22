# https://docs.influxdata.com/influxdb/cloud/reference/key-concepts/data-elements/
import re

_RE_VALID_CHARACTERS = re.compile(r"^[0-9a-zA-Z_.-]+$")

influxFieldKeyDict = {  # Zahlenwerte
    "temperature_C": None,
    "temperature_K": None,
    "pressure_Pa_rel": None,
    "pressure_Pa_abs": None,
    "resistance_Ohm": None,
    "voltage_V": None,
    "current_A": None,
    "flow_m3_per_s": None,
    "flow_mol_per_s": None,
    "powerOutage_s": None,
    "outage_trace_V": None,
    "power_W": None,
    "uptime_s": None,
    "number_i": None,
    "binary_state": None,  # True False
    "vibration_peak_AU": None,  # Integer
    "vibration_average_AU": None,  # Integer
    "humidity_pRH": None,
    "flow_ln_per_min": None,  # only for He flow sensor
    "total_ln": None,  # only for He flow sensor
}

influxTagKeyDict = {
    "room": ["A", "C15", "C17", "C18", "B15", "B16", "B17", "D24", "E9"],
    "setup": [
        "bigmom",
        "zeus",
        "titan",
        "tarzan",
        "emma",
        "bertram",
        "nele",
        "dobby",
        "bud",
        "charly",
        "anna",
        "werner",
        "sofia",
        "tabea",
        "fritz",
        "charlie",
        "broker",
        "HPT_nitrogen_tank",
    ],
    "position": None,  # z.B. "N2 exhaust tube"
    "user": ["pmaerki", "benekrat", "baehler", "lostertag", "hannav"],
    "quality": ["testDeleteLater", "use"],
}

measurements_example = [
    {
        "measurement": "pico_emil",  # a measurement has one 'measurement'. It is the name of the pcb.
        "fields": {
            "temperature_C": "23.5",
            "humidity_pRH": "88.2",
        },
        "tags": {
            "setup": "zeus",
            "room": "B15",
            "position": "hintenLinks",
            "user": "pmaerki",
        },
    },
    {
        "measurement": "pico_urs",  # a measurement has one 'measurement'. It is the name of the pcb.
        "fields": {
            "temperature_C": "25.5",
        },
        "tags": {
            "setup": "zeus",
            "room": "B16",
            "position": "hintenRechts",
            "user": "pmaerki",
        },
    },
]


def build_payload(measurements, validate=True):
    """
    https://docs.influxdata.com/influxdb/v2/reference/syntax/line-protocol/
    """
    assert isinstance(measurements, (list, tuple))

    def iter_measurements():
        for measurement in measurements:

            def iter_tags():
                yield measurement["measurement"]
                for tag_name, tag_value in measurement["tags"].items():
                    if validate:
                        assert _RE_VALID_CHARACTERS.match(tag_name), repr(tag_name)
                        assert _RE_VALID_CHARACTERS.match(tag_value), repr(tag_name)
                        valid_values = influxTagKeyDict[tag_name]
                        if valid_values is not None:
                            assert (
                                tag_value in valid_values
                            ), f"{tag_name}={tag_value} is not in {valid_values}"

                    yield f"{tag_name}={tag_value}"

            def iter_fields():
                for field_name, field_value in measurement["fields"].items():
                    if validate:
                        assert _RE_VALID_CHARACTERS.match(field_name), repr(field_name)
                        assert _RE_VALID_CHARACTERS.match(field_value), repr(
                            field_value
                        )
                        assert (
                            field_name in influxFieldKeyDict
                        ), f"field '{field_name}' is not in {influxFieldKeyDict}"
                    yield f"{field_name}={field_value}"

            yield ",".join(iter_tags()) + " " + ",".join(iter_fields())

    return "\n".join(iter_measurements())


if __name__ == "__main__":
    print(measurements_example)
    print(build_payload(measurements_example))

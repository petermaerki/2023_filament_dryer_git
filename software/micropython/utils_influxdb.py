# https://docs.influxdata.com/influxdb/cloud/reference/key-concepts/data-elements/
import re

_RE_VALID_CHARACTERS_NAME = re.compile(r"^[0-9a-zA-Z_\-\.]+$")
_RE_VALID_CHARACTERS_VALUE = re.compile(r"^[0-9a-zA-Z_\-\., ]*$")


def influxdb_escape(text: str) -> str:
    return text.replace(" ", r"\ ").replace(",", r"\,").replace("=", r"\=")


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
                meas_name = measurement["measurement"]
                assert not meas_name.startswith("_"), measurement
                yield meas_name

                for tag_name, tag_value in measurement["tags"].items():
                    if validate:
                        assert _RE_VALID_CHARACTERS_NAME.match(tag_name), tag_name
                        assert _RE_VALID_CHARACTERS_VALUE.match(tag_value), tag_value

                        tag_value = influxdb_escape(tag_value)

                    yield f"{tag_name}={tag_value}"

            def iter_fields():
                for field_name, field_value in measurement["fields"].items():
                    if validate:
                        assert _RE_VALID_CHARACTERS_NAME.match(field_name), field_name
                        if field_value.startswith('"'):
                            # There must be exactly on " at the beginning and one at the end!
                            assert field_value.count('"') == 2, field_value
                        else:
                            assert _RE_VALID_CHARACTERS_VALUE.match(field_value), repr(
                                field_value
                            )
                            field_value = influxdb_escape(field_value)

                    yield f"{field_name}={field_value}"

            yield ",".join(iter_tags()) + " " + ",".join(iter_fields())

    return "\n".join(iter_measurements())


if __name__ == "__main__":
    print(measurements_example)
    print(build_payload(measurements_example))

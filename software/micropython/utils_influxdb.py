# https://docs.influxdata.com/influxdb/cloud/reference/key-concepts/data-elements/
import re

_RE_VALID_CHARACTERS = re.compile(r"^[0-9a-zA-Z_.-]+$")


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

                    yield f"{tag_name}={tag_value}"

            def iter_fields():
                for field_name, field_value in measurement["fields"].items():
                    if validate:
                        assert _RE_VALID_CHARACTERS.match(field_name), repr(field_name)
                        if not field_value.startswith('"'):
                            assert _RE_VALID_CHARACTERS.match(field_value), repr(
                                field_value
                            )
                    yield f"{field_name}={field_value}"

            yield ",".join(iter_tags()) + " " + ",".join(iter_fields())

    return "\n".join(iter_measurements())


if __name__ == "__main__":
    print(measurements_example)
    print(build_payload(measurements_example))

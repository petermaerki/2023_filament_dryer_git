
2023-10-21_annotations_a.json

```flux
from(bucket: "filament_dryer")
  |> range(start: 2023-10-21T11:40:41Z, stop: 2023-10-21T11:40:59Z)
  |> filter(fn: (r) => r["_measurement"] == "dryer_prototype_v1.0_1")
```

```json
      {
        "name": "dryer_prototype_v1.0_1",
        "refId": "A",
        "fields": [
          {
            "name": "Time",
...
            "values": [
              1697888453551
            ],
          },
          {
            "name": "text",
            "type": "string",
            "typeInfo": {
              "frame": "string",
              "nullable": true
            },
            "labels": {
              "event": "annotation",
              "room": "B15",
              "setup": "zeus",
              "topic": "forward2influxdb"
            },
            "config": {},
            "values": [
              "Why: User Button: Forward to next state"
            ],
            "entities": {},
            "state": null
          }
        ],
        "length": 1
      },
```

```json
    {
      "name": "dryer_prototype_v1.0_1",
      "refId": "A",
      "fields": [
        {
          "name": "Time",
          "type": "time",
...
          "values": [
            1697888453551
          ],
        },
        {
          "name": "severity",
          "type": "string",
          "typeInfo": {
            "frame": "string",
            "nullable": true
          },
          "labels": {
            "event": "annotation",
            "room": "B15",
            "setup": "zeus",
            "topic": "forward2influxdb"
          },
          "config": {},
          "values": [
            "INFO"
          ],
          "entities": {},
          "state": null
        }
      ],
      "length": 1
    },
  ```
2023-10-21_annotations_b.json

```flux
from(bucket: "filament_dryer")
  |> range(start: 2023-10-21T11:40:41Z, stop: 2023-10-21T11:40:59Z)
```

```json
...
```

```
import "types"

from(bucket: "filament_dryer")
  |> range(start: v.timeRangeStart, stop:v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "${filament_dryer}")
  |> filter(fn: (r) => r._field != "statemachine")
//  |> filter(fn: (r) => r.event != "annotation")
//  |> filter(fn: (r) => r._field != "statemachine")
//  |> filter(fn: (r) => not types.isType(v: r._value, type: "string"))
//  |> filter(fn: (r) => types.isNumeric(v: r._value))
//  |> filter(fn: (r) => types.isNumeric(v: r._value))
//  |> aggregateWindow(every: 300s, fn: mean, createEmpty: false)
//  |> yield(name: "mean")
```
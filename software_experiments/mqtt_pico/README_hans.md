# MQTT

## Links
https://www.youtube.com/watch?v=vehHapPX_E8
https://www.youtube.com/watch?v=f7ws9pfLmJc
https://www.influxdata.com/integration/mqtt-telegraf-consumer/
https://github.com/influxdata/telegraf/tree/master/plugins/parsers/json_v2
http://mqtt-explorer.com/

## umqtt.simple
https://github.com/donskytech/micropython-raspberry-pi-pico/blob/main/umqtt.simple/main.py

## Topic parsing
https://www.donskytech.com/umqtt-simple-micropython-tutorial/#htoc-h
https://www.influxdata.com/blog/mqtt-topic-payload-parsing-telegraf/

## json_v2
https://www.mikrocontroller.net/topic/545947



# Vorschlag Peter

Via mqtt einen String schicken an Topic `influx`.

Der String hat dieses Format:

* https://github.com/nanophysics/pico_nano_monitor/blob/main/utils.py
* # payload = f"airSensor,sensorId=A0100,station=Harbor humidity=35.0658,temperature=37.2" 
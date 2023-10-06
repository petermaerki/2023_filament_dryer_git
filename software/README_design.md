# Design decisions

## WLAN and MQTT internet connections

* At micropython boot:
  * Start watchdog
  * wlan connect
  * mqtt broker connect
  * If failed:
    * Just remember, do not try to connect/reconnect
    * Run statemachine and do not access WLAN
    * After 1h: reboot
  * If success:
    * Run statemachine and access WLAN
    * If socket error during mqtt publish:
      * Just remember, do not try to connect/reconnect
    * After 1h: reboot

## Statemachine and Watchdog

* Statemachine
  * Start in state `drywait`
  * Just before `sensors.measure()`: Reset watchdog.

# User elements

* Button long: Reboot (and reconnect to wlan)
* Button short: Next state
* LED green: state `drywait`
* LED white: state `dryfan` 
* LED red: state `regenerate/cooldown`

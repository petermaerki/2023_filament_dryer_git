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

# WLAN in seperate thread

* No timer watchdog is required as the statemachine will feed() the wdt.

```
wdt_counter = 1
def feed():
  global wdt_counter
  if wdt_counter > 0:
     wdt_counter -= 1
  if wdt_counter == 0:
     wdt.feed()

Other core

def wlan_connect():
   wdt_counter = 10 # 10 times 8s
   wlan.connect()
   wdt_counter = 0
```
```
class SlowWdt:
  def __init__(self):
    self._start_ms: int = None
    self._expiration_ms: int = None

  def __activate__(self, expiration_ms: int):
    self._expiration_ms = expiration_ms
    self._start_ms = time.now()
  
  def feed(self):
    duration_ms = diff(time.now, self._start_ms) 
    if duration_ms > self._expiration_ms:
       reboot

def feed():
  global wdt_counter
  if wdt_counter > 0:
     wdt_counter -= 1
  if wdt_counter == 0:
     wdt.feed()

def wlan_connect():
  wdt_wlan_start_ms = time.now()
  wlan.connect()
  wdt_wlan_start_ms = None
```
** Filesystem size

* Filenamen dryer jlcpcb: 8 MBytes
* Raspberry Pi Pico: 2 MBytes

* 2023-09-10a_logdata.txt -> 842_681Bytes
* Log every 2 seconds
* Duration: 18_798_791ms -> 5.22h
* Disk size: 1.4MBytes
* Max duration: 5.22h * 1.4MBytes / 842_681Bytes = 5.22*1_400_000/842_681 = 8.6h

* 10s statt 2s -> 43h statt 8.6h

** How to run a test

* VSCode: `run_from_pc`
* Prepare / format filesystem: Micropython: `rf()`
* VSCode: `run_from_pc`
* Let experiment run
* Check 'disk free': Micropython: `df()`
* Stop experiment: Micropython: `stop()`

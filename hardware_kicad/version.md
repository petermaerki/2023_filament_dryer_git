# 2023-07-16 v0.1

Manuelle Korrekturen
USB3 Muffe nach hinten verschoben
Um 90 Grad gedreht: U1, U4, U5, U6

# 2023-07-17 v0.2

Fix Footprint of R Heating
Add R for 1wire


Manuelle Korrekturen
USB3 Muffe nach hinten verschoben
Um 90 Grad gedreht: U1, U4, U5, U6


# 2023-07-18 v0.3

Final steps

* Schema Editor: File -> Page Settings: Update Revision & issue date
* Schema Editor: Inspect -> Electrical Rule Checker -> 0 Errors, 0 Warnings
* PCB Editor: File -> Page Settings: Update Revision & issue date
* PCB Editor: Tools -> Clean up tracks & vias -> check all
* PCB Editor: Inspect -> Design Rule Checker -> 0 Errors, 0 Warnings
* PCB Editor: Button "Fabrication Toolkit"

Manuelle Korrekturen in JLC
USB3 nach hinten verschoben
Um 90 Grad gedreht: U1, U4, U5, U6

# 2023-09-08 v0.6

Probleme:
 * FET Q1-Q8: Pins falsch.
 * FET Q1-Q8: Falsch: https://ngspice.sourceforge.io/docs/ngspice-manual.pdf
 * FET Q1-Q8: Korrekt: https://datasheet.lcsc.com/lcsc/1810010522_Infineon-Technologies-IRLML6244TRPBF_C143946.pdf
 * R1 4.7k: Zu gross, 2k ist ok.
 * Warum hat JLCPCB Komponenten verdreht?
 * Schrauben für Gehäuse: Sperrzone um Kurzschluss zu verhindern.
 * Schema: HT_SILICAGEL_SCA -> HT_SILICAGEL_SDA

 * Konsistente Namensgebung: SILICAGEL, FILAMENT, AMBIENT. Falsch ist BOARD, EXTs

# 2023-09-28 v1.0
  * GPIO_FAN_AMBIENT is missing!
  * Ambient Sensor: C2 ist unter dem Gehäuse!
  * Löcher unter Pico sind unnütz!

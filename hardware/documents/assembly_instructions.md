# Assembly instructions
## Circuit Board
Raspberry Pi Pico W mit MicroPython v1.21.0

* Ordner `software\micropython`: `config_secrets.py` auspacken/ausfüllen. In Thonny, `config_secrets.py` auf das Filesystem kopieren.
* In VSCode Debug: `run_from_pc`: Dies kopiert alle Files auf den pico.
* Jetzt starten der pico und wird als erstes mit dem Wlan verbinden und die aktuelle Version aus dem Web herunterladen.

* Um mit `run_from_pc` debuggen zu können, `False` eintragen bei:
```python
main.py
ENABLE_APP_PACKAGE_UPDATE = True
ENABLE_WDT = True
```

Buchsenleisten und Stiftenleisten fuer RP Pico W  
Micro USB Kabel

Thermal Fuse D139-002 (141C), soldered 7 mm above circuit board surface. See Picture.

3D Prints:
* 20240619a_filament_dryer_silicagel-teil_oben_ASA
* 20240619a_filament_dryer_silicagel-teil_unten_PETG
* 20240619a_filament_dryer_silicagel-barriere_PETG
* 20240619a_filament_dryer_silicagel-filterpapierklemmer_PETG
* 20240619a_filament_dryer_silicagel-filterpapierklemmer_mirrored_PETG

Filterpapier  
20231027_filterpapier_abmessung.txt

EVA Foam, 2 mm thick, cut to size:  
20231028_schneidelehre.pdf

EVA Foam 3mm, cut to size, to make it tight against the plastic casing.
20231028_schneidelehre.pdf

Fans
```
2 (or 3 piece)
Fan 2510 (25 mm x 25 mm x 10 mm) 5V slow running fan, 2 pin cable.
Cheap from aliexpress or
Distrelec 301-48-121  MF25100V2-1000U-A99
```

Screws
* 5   M3x20 Linsenkopf (oberes und unteres Teil)
* 2   M3x8 Linsenkopf (Balken)
* 4   M3x10 Linsenkopf (für die Montage in der Plastikbox)



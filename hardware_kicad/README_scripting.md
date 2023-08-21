
https://dev-docs.kicad.org/en/python/pcbnew/

https://github.com/mcbridejc/kicad_component_layout/blob/master/examples/led-circle/layout.py


--------------
```python

import pcbnew; print(pcbnew.PLUGIN_DIRECTORIES_SEARCH)
/usr/share/kicad/scripting
/usr/share/kicad/scripting/plugins
/home/maerki/.config/kicad/7.0/scripting
/home/maerki/.config/kicad/7.0/scripting/plugins
/home/maerki/.local/share/kicad/7.0/scripting
/home/maerki/.local/share/kicad/7.0/scripting/plugins
/home/maerki/.local/share/kicad/7.0/3rdparty/plugins


import pcbnew
ap = pcbnew.ActionPlugin()

pcb = pcbnew.GetBoard()

footprints = pcb.GetFootprints()
for footprint in footprints: print(footprint)

refdes = ""
mod = pcb.FindFootprintByReference(refdes)



footprint.GetPath().AsString()
'/85b4834f-1429-4c28-a1bb-14cdbf0ecd65'

footprint.GetDescription()
'LED SMD 1206 (3216 Metric), square (rectangular) end terminal, IPC_7351 nominal, (Body size source: http://www.tortai-tech.com/upload/download/2011102023233369053.pdf), generated with kicad-footprint-generator'

footprint.GetLayerName()
'B.Cu'

footprint.GetCenter()
VECTOR2I(192923069, 70317037)

footprint.GetReferenceAsString()
'D7'

footprint.GetReference()
'D7'

footprint.GetX()
192947000
footprint.GetY()
70292000

footprint.GetOrientationDegrees()
36.0


mod = pcb.FindFootprintByReference('D8')
mod.SetOrientationDegrees(0.0)

execfile()

```
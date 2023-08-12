# FreeCAD

## PCB -> KiCad

### FreeCAD
FreeCAD: Open `20230802b_filament_dryer_silicagel.FCStd`

In Python Console:

```python
objs=[]
objs.append(FreeCAD.getDocument("_0230812a_filament_dryer_silicagel").getObject("Sketch005"))
import importDXF
importDXF.export(objs, u"/tmp/board.dxf")

del objs
```

### KiCad

* Menu `File -> Import Graphics`
  * `/tmp/board.dxf`
  * At `0`, `0`
  * Layer `Edge.Cuts`
  * Import scale: `1`
  * `check` Group Items
  * Default line width `0.2 mm`
  * Default units: `Millimeters`

TODO: Where to position?
TODO: Keepout rules

## Footprint -> KiCad

### FreeCAD
FreeCAD: Open `20230812a_filament_dryer_silicagel.FCStd`

In Python Console:

```python
objs=[]
objs.append(FreeCAD.getDocument("_0230812a_filament_dryer_silicagel").getObject("Body"))
import importDXF
importDXF.export(objs,u"/tmp/dryer_3d.dxf")

del objs
```

### KiCad

Footprint Editor

* Menu `New Footprint...`
  * Name: `dryer_3d`
  * Footprint type `Other`

* Menu `File -> Import Graphics`
  * `/tmp/dryer_3d.dxf`
  * At `0`, `0`
  * Layer `F.Silkscreen`
  * Import scale: `1`
  * `check` Group Items
  * Default line width `0.2 mm`
  * Default units: `Millimeters`

TODO: Where to position?
TODO: Keepout rules

## 3D Model -> KiCad

```python
objs=[]
objs.append(FreeCAD.getDocument("_0230812a_filament_dryer_silicagel").getObject("Body"))
import ImportGui
ImportGui.export(objs,u"/tmp/dryer_3d.step")

del objs
```

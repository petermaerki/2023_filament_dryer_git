# FreeCAD

## PCB -> KiCad

### FreeCAD

In Python Console:

```python
objs=[]
objs.append(FreeCAD.getDocument("_0230812a_filament_dryer_silicagel").getObject("Sketch005"))
import importDXF
importDXF.export(objs, u"/tmp/pcb.dxf")

del objs
```

### KiCad

* Menu `File -> Import Graphics`
  * `/tmp/dryer_board.dxf`
  * At `0`, `0`
  * Layer `Edge.Cuts`
  * Import scale: `1`
  * `check` Group Items
  * Default line width `0.2 mm`
  * Default units: `Millimeters`

Flip horizontally!

## Footprint -> KiCad

### FreeCAD

In Python Console:

```python
objs=[]
objs.append(FreeCAD.getDocument("_0230812a_filament_dryer_silicagel").getObject("Body"))
import importDXF
importDXF.export(objs,u"/tmp/dryer_print3d.dxf")

del objs
```

In VSCode:

`mv /tmp/dryer_print3d.dxf ./hardware_kicad/Parts/drayer_print_3d`

### KiCad

Footprint Editor

* Menu `New Footprint...`
  * Name: `dryer_print3d`
  * Footprint type `Other`

* Menu `File -> Import Graphics`
  * `/tmp/dryer_print3d.dxf`
  * At `0`, `0`
  * Layer `F.Silkscreen`
  * Import scale: `1`
  * `check` Group Items
  * Default line width `0.2 mm`
  * Default units: `Millimeters`

## 3D Model -> KiCad

### FreeCAD

In Python Console:

```python
objs=[]
objs.append(FreeCAD.getDocument("_0230812a_filament_dryer_silicagel").getObject("Body"))
import ImportGui
ImportGui.export(objs,u"/tmp/dryer_print3d.step")

del objs
```

In VSCode:

`mv /tmp/dryer_print3d.step ./hardware_kicad/Parts/drayer_print_3d`

### KiCad

* Edit Footprint Properties
* Add 3D Model
* Rotation Y: `180`

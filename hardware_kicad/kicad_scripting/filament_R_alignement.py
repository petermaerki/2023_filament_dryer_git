"""
Place this script in folder:
~/.config/kicad/7.0/scripting/scripting/plugins/filament_neopixel_alignement.py
"""
import pcbnew
import importlib

class NeopixelLayout(pcbnew.ActionPlugin):
    """
    Uses data in layout.yaml (location in your kicad project directory) to layout footprints
    """

    def defaults(self):
        self.name = "filament_dryer R Alignement"
        self.category = "AA Modify PCB"
        self.description = "Salami Alignement of R"
        self.show_toolbar_button = True

    def Run(self):
        print(f"This is kicad plugin {__name__}")

        inner_module = importlib.import_module("filament_R_alignement_inner")
        importlib.reload(inner_module)

        print(f"reload module {inner_module.__name__}")

        inner_module.run()


NeopixelLayout().register()

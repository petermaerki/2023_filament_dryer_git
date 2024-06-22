# https://gitlab.com/transistorgrab/kicad-dxf-cleaner/-/blob/main/DXFcleaner.py

## DXF cleaner
#  this is a tool that takes DXF files (generated by Kicad) and looks at entpoints of ARCs and LINEs
#  if the endpoints are within a given tolerance the endpoints of the LINEs are placed at the exact same coordinate
#  as the endpoint of the ARC. ARCs points are not moved – only the connecting LINEs.
#  CIRCLEs are left alone completely

# author: AnSc
# date: 2023-06-24
# requires: ezdxf (depends on pyparser and typing_extensions)

import ezdxf
import pathlib
import math


base_unit = 0.001  ## base unit is mm. this needs to be used for calculating the final numbers in correct lenghts eg. µm and nm and not "micro millimeter"
## at below which distance in mm should two points regarded as at the same coordinate
max_tolerance = 0.01

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

infile = DIRECTORY_OF_THIS_FILE / "dryer_board_fixed.dxf"
outfile = DIRECTORY_OF_THIS_FILE / "dryer_board_fixed_cleaned.dxf"


doc = ezdxf.readfile(infile)
msp = doc.modelspace()

## some statistics
arcs = msp.query("ARC")
lines = msp.query("LINE")
circles = msp.query("CIRCLE")
print(
    "Found "
    + str(len(arcs))
    + " arcs, "
    + str(len(lines))
    + " lines and "
    + str(len(circles))
    + " circles in the drawing."
)


def distance(p1, p2) -> float:
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def is_equal(p1, p2) -> bool:
    # return distance(p1, p2) == 0.0
    return distance(p1, p2) < 0.000_1


# Remove short lines
short_lines = []
for line in lines:
    if distance(line.dxf.start, line.dxf.end) < 1.0:
        short_lines.append(line)

for line in short_lines:
    msp.delete_entity(line)

print(f"From {len(lines)} are {len(short_lines)} short lines.")
lines = msp.query("LINE")


# Remove duplicate lines
duplicate_lines = []
for idx1, line1 in enumerate(lines):

    def is_duplicate():
        for line2 in lines[idx1 + 1 :]:
            assert line1 is not line2

            if is_equal(line1.dxf.start, line2.dxf.start):
                if is_equal(line1.dxf.end, line2.dxf.end):
                    # print(f"Duplicate line {line1}")
                    return True
        return False

    if not is_duplicate():
        continue

    duplicate_lines.append(line1)

for line in duplicate_lines:
    msp.delete_entity(line)

print(f"From {len(lines)} are {len(duplicate_lines)} duplicate lines.")
lines = msp.query("LINE")


# Remove duplicate arcs
duplicate_arcs = []
for idx1, arc1 in enumerate(arcs):

    def is_duplicate():
        for arc2 in arcs[idx1 + 1 :]:
            assert arc1 is not arc2

            if abs(arc1.dxf.radius - arc2.dxf.radius) < 0.000_1:
                if abs(arc1.dxf.start_angle - arc2.dxf.start_angle) < 0.000_1:
                    if abs(arc1.dxf.end_angle - arc2.dxf.end_angle) < 0.000_1:
                        if is_equal(arc1.dxf.center, arc2.dxf.center):
                            return True
        return False

    if not is_duplicate():
        continue

    duplicate_arcs.append(arc1)

for arc in duplicate_arcs:
    msp.delete_entity(arc)

print(f"From {len(arcs)} are {len(duplicate_arcs)} duplicate arcs.")
arcs = msp.query("ARC")

# Remove duplicate circles
duplicate_circles = []
for idx1, circle1 in enumerate(circles):

    def is_duplicate():
        for circle2 in circles[idx1 + 1 :]:
            assert circle1 is not circle2

            if abs(circle1.dxf.radius - circle2.dxf.radius) < 0.000_1:
                if is_equal(circle1.dxf.center, circle2.dxf.center):
                    return True
        return False

    if not is_duplicate():
        continue

    duplicate_circles.append(circle1)

for circle in duplicate_circles:
    msp.delete_entity(circle)

print(f"From {len(circles)} are {len(duplicate_circles)} duplicate circles.")
circles = msp.query("ARC")

print(f"writing output to file: {outfile}")
doc.saveas(outfile)
print("finished")
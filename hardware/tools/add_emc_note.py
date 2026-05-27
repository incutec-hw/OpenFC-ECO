#!/usr/bin/env python3
"""Add EMC checklist textbox to root schematic. Non-destructive."""
import kicad_sch_api as ksa
import os

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "OpenFC.kicad_sch")

CHECKLIST = """EMC CHECKLIST - OpenFC-Lite (see tools/EMC_CHECKLIST.md for details)

BUCKS (U3/U4, L2/L3):
- CIN+COUT GND: local top-side island, 2 stitching vias to inner plane
- SW node: minimum copper area, <5mm, no GND pour under SW or inductor
- L2 and L3 >5mm apart
- FB trace away from SW, shielded by GND plane on adjacent layer

IMU (U9 LSM6DSV16X):
- Place >10mm from any switch node or inductor (L1/L2/L3)
- Over continuous inner GND plane, no splits
- 100nF VDD + 100nF VDDIO within 1mm of pins
- SPI0 routed tight with GND ref, NOT over SW nodes

CRYSTAL X1 (12MHz):
- Directly under XIN/XOUT pins, <3mm stubs
- GND guard ring with 2+ vias
- Load caps same side as crystal
- No ground flood BETWEEN XIN/XOUT traces

USB:
- 27ohm series R immediately next to MCU pins 66/67
- 90ohm diff pair, continuous GND plane beneath entire length
- USBLC6 ESD AT connector (not near MCU)
- GND stitch vias flanking any layer transition

ADC (VBAT/CURR/RSSI/EXT):
- RC filters within 5mm of MCU pins
- Keep away from SW nodes

MOTOR OUTPUTS M1-M4:
- Add 22-33ohm series R at MCU (dropped from 0 ohm)
- Route over GND plane, physical distance from IMU

ESD/PROTECTION (ADD):
- TVS 5V uni-dir diode on every external pad: RX, SBUS, LED, Beeper,
  Current, RSSI, Video
- Series 100-470ohm on LED strip + beeper outputs

POWER RAIL FILTERING (ADD):
- Bulk 47-100uF low-ESR electrolytic at BATT input
- Ferrite bead + bulk cap at each connector output (VTX, RX)

GND PLANE:
- Solid continuous inner GND (layer 2) under top signals, no splits
- No analog/digital GND island split (modern practice = single plane)
- Heavy via stitching every 5-10mm

MUST-FIX before fab:
1. Buck hot-loop GND islands + separate stitching vias
2. SW node copper minimized, no GND pour under SW/L
3. IMU >=10mm from all switch nodes
4. USB ESD at connector, GND continuity under diff pair
5. Crystal guard ring under XIN/XOUT
"""

def main():
    print(f"Loading {ROOT}")
    sch = ksa.load_schematic(ROOT)

    # Place bottom-left, below all existing sheets
    # Existing sheet bounds: y max ~162.56, x: 31 to 218
    # A3 page ~420x297 or A4 297x210
    text_uuid = sch.add_text_box(
        text=CHECKLIST,
        position=(12.7, 170.18),
        size=(250.0, 100.0),
        font_size=1.0,
        margins=(1.5, 1.5, 1.5, 1.5),
        stroke_width=0.15,
        stroke_type="default",
        justify_horizontal="left",
        justify_vertical="top",
    )
    print(f"Added text box uuid={text_uuid}")

    sch.save(ROOT)
    print(f"Saved {ROOT}")


if __name__ == "__main__":
    main()

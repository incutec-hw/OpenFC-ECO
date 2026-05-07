#!/usr/bin/env python3
"""
Rebuild blackbox.kicad_sch with the SD card slot circuit (TF-021B-H265).

The original sub-sheet was accidentally deleted. This script recreates it
using kicad-sch-api + post-processing for bus entries (not serialized by API).

Root sheet pins (must match hierarchical labels in sub-sheet):
  BB_CS                    -> input
  SPI1{SCK,MOSI,MISO}     -> input (bus)

PCB net names:
  /BLACKBOX/BB_CS, /BLACKBOX/SPI1.SCK, /BLACKBOX/SPI1.MOSI, /BLACKBOX/SPI1.MISO
"""

import kicad_sch_api as ksa
import os
import uuid as uuid_mod

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HARDWARE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT = os.path.join(HARDWARE_DIR, "blackbox.kicad_sch")

# UUIDs from PCB (must match for zero-diff import)
UUIDS = {
    "Card2": "1ec1adf4-cd1a-492a-816f-22ff8bdb6a5a",
    "R1": "4901177e-bac2-4009-b96f-6ea3fff98e44",
    "R2": "a7c15a48-ef6b-4046-9057-c4903e96ba7a",
    "R3": "1d8aa755-10b9-4bbd-ab89-eaa6689f9242",
    "C1": "ac16b3cf-0d18-48cc-8732-9faf976337a5",
}


def new_uuid():
    return str(uuid_mod.uuid4())


def build_schematic():
    sch = ksa.create_schematic("BLACKBOX")
    sch.library.add_library_path(os.path.join(HARDWARE_DIR, "lib.kicad_sym"))

    # ================================================================
    # Layout plan (all coordinates in mm, KiCad grid 2.54mm):
    #
    # TF-021B-H265 symbol placed at (115, 75)
    # Left pins (1-4, 10) at x=101.03, Right pins (5-9) at x=128.97
    #
    # Left side:
    #   Pullup R1 (horizontal) between pin 1 and +3.3V rail
    #   Pullup R2 (horizontal) between pin 2 and +3.3V rail
    #   BB_CS hierarchical label connects to pin 2 net
    #   C1 decoupling near pin 4 (VDD)
    #   MOSI label + wire from pin 3 routed to right bus
    #
    # Right side:
    #   Pullup R3 (horizontal) between pin 8 and +3.3V rail
    #   SPI bus (vertical) with bus entries for SCK, MOSI, MISO
    #   SPI1{SCK,MOSI,MISO} hierarchical label at bus
    # ================================================================

    CARD_X, CARD_Y = 115, 75

    # --- SD card slot ---
    card = sch.components.add(
        "lib:TF-021B-H265", "U2", "TF-021B-H265",
        position=(CARD_X, CARD_Y),
        footprint="lib:TF-SMD_TF-021B-H265",
        component_uuid=UUIDS["Card2"],
    )
    card.set_property("LCSC", "C498185")
    card.set_property("Datasheet",
        "https://lcsc.com/product-detail/New-Arrivals_SOFNG-TF-021B-H265_C498185.html")

    # Get pin positions
    pins = {}
    for pnum in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        pos = sch.get_component_pin_position("U2", pnum)
        if pos:
            pins[pnum] = (round(pos.x, 2), round(pos.y, 2))

    print("Pin positions:")
    for k, v in pins.items():
        print(f"  pin {k}: {v}")

    # --- Pullup resistors (horizontal, 90 deg rotation) ---
    # R1 on pin 1 (DAT2), R2 on pin 2 (CS), R3 on pin 8 (DAT1)
    for ref, pcb_ref, pin, side in [
        ("R1", "R1", "1", "left"),
        ("R2", "R2", "2", "left"),
        ("R3", "R3", "8", "right"),
    ]:
        px, py = pins[pin]
        if side == "left":
            rx = px - 10.16
        else:
            rx = px + 10.16

        r = sch.components.add(
            "Device:R", ref, "10k",
            position=(rx, py),
            footprint="Capacitor_SMD:C_0201_0603Metric",
            rotation=90.0,
            component_uuid=UUIDS[pcb_ref],
        )
        r.set_property("LCSC", "C106225")

    # --- Decoupling cap C1 (vertical, near VDD pin 4) ---
    c1_x = pins["4"][0] - 7.62
    c1_y = pins["4"][1] + 2.54
    c1 = sch.components.add(
        "Device:C", "C1", "100n",
        position=(c1_x, c1_y),
        footprint="Capacitor_SMD:C_0201_0603Metric",
        rotation=0.0,
        component_uuid=UUIDS["C1"],
    )
    c1.set_property("LCSC", "C76939")

    # --- Power symbols ---
    # Get resistor pin 2 positions (the end away from the card = +3.3V end)
    for ref in ["R1", "R2", "R3"]:
        p2 = sch.get_component_pin_position(ref, "2")
        if p2:
            sch.components.add("power:+3.3V", None, "+3.3V",
                             position=(round(p2.x, 2), round(p2.y, 2)))

    # +3.3V at VDD (pin 4) - connect via C1
    c1_p1 = sch.get_component_pin_position("C1", "1")
    if c1_p1:
        sch.components.add("power:+3.3V", None, "+3.3V",
                         position=(round(c1_p1.x, 2), round(c1_p1.y, 2)))

    # GND at VSS (pin 6), shell (pins 9, 10), C1 pin 2
    for pin_num in ["6", "9", "10"]:
        sch.components.add("power:GND", None, "GND", position=pins[pin_num])

    c1_p2 = sch.get_component_pin_position("C1", "2")
    if c1_p2:
        sch.components.add("power:GND", None, "GND",
                         position=(round(c1_p2.x, 2), round(c1_p2.y, 2)))

    # --- Wires ---
    # Connect resistor pin 1 to card pins
    sch.add_wire_between_pins("R1", "1", "U2", "1")
    sch.add_wire_between_pins("R2", "1", "U2", "2")
    sch.add_wire_between_pins("R3", "1", "U2", "8")

    # C1 pin 1 to card VDD (pin 4)
    if c1_p1:
        sch.add_wire((round(c1_p1.x, 2), round(c1_p1.y, 2)), pins["4"])

    # --- BB_CS hierarchical label ---
    # Place to the left of R2, connecting to pin 2 net
    r2_p2 = sch.get_component_pin_position("R2", "2")
    if r2_p2:
        label_x = round(r2_p2.x, 2) - 5.08
        label_y = round(r2_p2.y, 2)
        sch.add_hierarchical_label("BB_CS", position=(label_x, label_y),
                                   shape="input", rotation=180)
        sch.add_wire((label_x, label_y), (round(r2_p2.x, 2), label_y))

    # --- SPI net labels (will connect to bus entries in post-process) ---
    # Place net labels to the right of card pins, offset for bus entry connection
    # Bus will be at x = pins["5"][0] + 15.24
    # Bus entries extend (-2.54, -2.54) from bus to net wire
    bus_x = pins["5"][0] + 12.7
    net_x = bus_x - 2.54  # where net labels sit

    # SCK (pin 5) - direct horizontal wire from pin to net label
    sck_y = pins["5"][1]
    sch.add_label("SPI1.SCK", position=(net_x, sck_y))
    sch.add_wire(pins["5"], (net_x, sck_y))

    # MISO (pin 7) - direct horizontal wire from pin to net label
    miso_y = pins["7"][1]
    sch.add_label("SPI1.MISO", position=(net_x, miso_y))
    sch.add_wire(pins["7"], (net_x, miso_y))

    # MOSI (pin 3) - left side pin, route around to right side
    mosi_y = miso_y - 2.54  # above MISO on the bus
    sch.add_label("SPI1.MOSI", position=(net_x, mosi_y))
    # Route: pin 3 -> left -> up -> across to net_x
    route_x = pins["3"][0] - 5.08
    sch.add_wire(pins["3"], (route_x, pins["3"][1]))
    sch.add_wire((route_x, pins["3"][1]), (route_x, mosi_y))
    sch.add_wire((route_x, mosi_y), (net_x, mosi_y))

    # --- SPI bus hierarchical label ---
    # Place at the right end of the bus
    bus_label_y = sck_y  # middle of bus
    sch.add_hierarchical_label("SPI1{SCK,MOSI,MISO}",
                               position=(bus_x + 5.08, bus_label_y),
                               shape="input", rotation=0)

    # Save base schematic
    sch.save(OUTPUT)
    print(f"\nSaved base schematic to {OUTPUT}")

    # Post-process: add bus entries, bus wires, fix Card2 ref
    postprocess(bus_x, net_x, sck_y, miso_y, mosi_y, bus_label_y)


def postprocess(bus_x, net_x, sck_y, miso_y, mosi_y, bus_label_y):
    with open(OUTPUT, "r") as f:
        content = f.read()

    # Fix Card2 reference
    content = content.replace('"Reference" "U2"', '"Reference" "Card2"')
    content = content.replace('(reference "U2")', '(reference "Card2")')

    # Build bus entries and bus wires to inject
    # Bus entries go from bus (bus_x) to net wire (net_x = bus_x - 2.54)
    # size = (-2.54, -2.54) means entry goes left and up from bus position
    # For our layout: bus is vertical at bus_x
    # Each entry starts at (bus_x, entry_y + 2.54) and extends to (net_x, entry_y)
    # Actually: bus_entry position is where the entry starts on the bus,
    # size is the offset to the net end

    bus_entries = ""
    for entry_y in [sck_y, miso_y, mosi_y]:
        # Bus entry: starts on bus at (bus_x, entry_y + 2.54),
        # extends to (bus_x - 2.54, entry_y) = (net_x, entry_y)
        bus_entries += f"""\t(bus_entry
\t\t(at {bus_x} {entry_y + 2.54})
\t\t(size -2.54 -2.54)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)
"""

    # Bus wires (vertical segments connecting bus entries)
    bus_top = mosi_y + 2.54  # top of bus (above highest entry)
    bus_bot = sck_y + 2.54   # bottom of bus (at lowest entry)
    bus_wires = f"""\t(bus
\t\t(pts
\t\t\t(xy {bus_x} {bus_top - 2.54}) (xy {bus_x} {bus_bot + 2.54})
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)
"""

    # Bus wire from vertical bus to hierarchical label
    bus_wires += f"""\t(bus
\t\t(pts
\t\t\t(xy {bus_x} {bus_label_y}) (xy {bus_x + 5.08} {bus_label_y})
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{new_uuid()}")
\t)
"""

    # Inject before the first (label or (hierarchical_label
    inject_point = content.find("\t(label ")
    if inject_point < 0:
        inject_point = content.find("\t(hierarchical_label ")
    if inject_point < 0:
        # Fallback: inject before closing paren
        inject_point = content.rfind(")")

    content = content[:inject_point] + bus_entries + bus_wires + content[inject_point:]

    with open(OUTPUT, "w") as f:
        f.write(content)

    print("Post-processed:")
    print("  - Fixed Card2 reference")
    print("  - Added 3 bus entries")
    print("  - Added bus wires")


if __name__ == "__main__":
    build_schematic()

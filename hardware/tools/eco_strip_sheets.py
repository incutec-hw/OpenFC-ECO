#!/usr/bin/env python3
"""
OpenFC-Lite: Remove sub-sheets not needed for ECO variant.

Removes: baro, blackbox, elrs, leds (WS2812B), compass
Keeps: rp2350a, power, pads, osd, imu

Uses kicad-skip to parse and rewrite the root schematic.
After running, open in KiCad and clean up any dangling wires (ERC will flag them).
"""

import sys
import os

try:
    from skip import Schematic
except ImportError:
    print("ERROR: kicad-skip not installed. Run: pip3 install kicad-skip")
    sys.exit(1)

# Sheets to remove (by Sheetfile value)
REMOVE_FILES = {
    "baro.kicad_sch",
    "blackbox.kicad_sch",
    "elrs.kicad_sch",
    "leds.kicad_sch",
    "compass.kicad_sch",
}

def main():
    sch_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "OpenFC.kicad_sch")

    if not os.path.exists(sch_path):
        print(f"ERROR: {sch_path} not found")
        sys.exit(1)

    print(f"Loading: {sch_path}")
    sch = Schematic(sch_path)

    # Collect UUIDs and pin locations of sheets to remove
    remove_uuids = []
    remove_pin_locations = []

    for s in sch.sheet:
        sheetfile = None
        sheetname = None
        for p in s.property:
            if p.name == "Sheetfile":
                sheetfile = p.value
            if p.name == "Sheetname":
                sheetname = p.value

        if sheetfile in REMOVE_FILES:
            uuid_str = str(s.uuid)
            remove_uuids.append(uuid_str)
            print(f"  Will remove: {sheetname} ({sheetfile}) uuid={uuid_str[:12]}...")

            # Collect pin locations for wire removal
            for item in s:
                if hasattr(item, 'name') and 'pin' in str(type(item)).lower():
                    pass  # kicad-skip pin handling varies
        else:
            sheetname_display = sheetname or "?"
            print(f"  Keeping: {sheetname_display} ({sheetfile})")

    if not remove_uuids:
        print("Nothing to remove!")
        return

    # Remove sheets from the tree by filtering the raw s-expression
    # kicad-skip's remove API can be tricky, so we work at the tree level
    tree = sch.tree

    # Find and remove sheet elements
    indices_to_remove = []
    for i, elem in enumerate(tree):
        if hasattr(elem, '__iter__') and len(elem) > 0:
            # Check if this is a sheet element
            try:
                from sexpdata import Symbol
                if isinstance(elem[0], Symbol) and str(elem[0]) == 'sheet':
                    # Check UUID
                    for sub in elem:
                        if hasattr(sub, '__iter__') and len(sub) > 0:
                            if isinstance(sub[0], Symbol) and str(sub[0]) == 'uuid':
                                uuid_val = str(sub[1])
                                if uuid_val in remove_uuids:
                                    indices_to_remove.append(i)
            except (TypeError, IndexError):
                continue

    # Also find and remove sheet_instances for removed sheets
    for i, elem in enumerate(tree):
        if hasattr(elem, '__iter__') and len(elem) > 0:
            try:
                from sexpdata import Symbol
                if isinstance(elem[0], Symbol) and str(elem[0]) == 'sheet_instances':
                    # Filter out paths referencing removed UUIDs
                    new_instances = [elem[0]]  # keep the 'sheet_instances' symbol
                    for sub in elem[1:]:
                        if hasattr(sub, '__iter__') and len(sub) > 0:
                            path_str = str(sub)
                            should_keep = True
                            for uuid in remove_uuids:
                                if uuid in path_str:
                                    should_keep = False
                                    break
                            if should_keep:
                                new_instances.append(sub)
                    # Replace in-place
                    elem.clear()
                    elem.extend(new_instances)
            except (TypeError, IndexError):
                continue

    # Remove sheets (reverse order to maintain indices)
    removed_count = 0
    for i in sorted(indices_to_remove, reverse=True):
        del tree[i]
        removed_count += 1

    print(f"\nRemoved {removed_count} sheet instances")

    # Write back
    sch.write(sch_path)
    print(f"Written: {sch_path}")
    print("\nNOTE: Open in KiCad and run ERC to find/clean up dangling wires.")
    print("Also remove wires that previously connected to removed sheet pins.")

if __name__ == "__main__":
    main()

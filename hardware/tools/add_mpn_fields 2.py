#!/usr/bin/env python3
"""
Add MPN and Manufacturer properties to KiCad schematic symbols.

Reads LCSC/LCSC_Part properties from all .kicad_sch files, looks up the
MPN and manufacturer via the jlcsearch API, and writes them back as new
symbol properties using kicad-skip.

Usage:
    python3 add_mpn_fields.py                    # dry-run (default)
    python3 add_mpn_fields.py --write            # write changes to files
    python3 add_mpn_fields.py --cache-only       # just build the API cache
    python3 add_mpn_fields.py --write --skip-api # use cached data only
"""

from __future__ import annotations

import argparse
import copy
import glob
import json
import os
import sys
import time
from pathlib import Path

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

from sexpdata import Symbol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skip import Schematic

HARDWARE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = HARDWARE_DIR / "tools" / ".lcsc_mpn_cache.json"
API_BASE = "https://jlcsearch.tscircuit.com/api/search"
API_DELAY = 0.6

# Manufacturer ID -> name mapping (from LCSC/jlcsearch manufacturer_id field)
MANUFACTURER_IDS: dict[int, str] = {
    4: "Murata Electronics",
    7: "Samsung Electro-Mechanics",
    10: "YAGEO",
    14: "TDK",
    18862: "Raspberry Pi",
    27: "Espressif Systems",
    521: "Semtech",
    23: "STMicroelectronics",
    99: "Bosch Sensortec",
    21: "Texas Instruments",
    108: "onsemi",
    1502: "WPMtek",
    6: "Winbond",
    29: "Diodes Incorporated",
    1115: "Abracon",
    3: "Vishay",
    5: "Panasonic",
    8: "Taiyo Yuden",
    9: "KEMET",
    11: "Rohm",
    12: "Nexperia",
    15: "Microchip",
    16: "NXP",
    17: "Infineon",
    19: "Renesas",
    22: "Analog Devices",
    24: "Bourns",
    30: "Lite-On",
    33: "JST",
    1866: "YXC",
    6458: "XINGLIGHT",
}

# MPN prefix -> manufacturer (preferred over manufacturer_id)
MPN_PREFIX_MAP: dict[str, str] = {
    # Passives - Murata
    "GRM": "Murata Electronics",
    "GCM": "Murata Electronics",
    "LQG": "Murata Electronics",
    "LQW": "Murata Electronics",
    "BLM": "Murata Electronics",
    # Passives - Samsung
    "CL0": "Samsung Electro-Mechanics",
    "CL1": "Samsung Electro-Mechanics",
    # Passives - YAGEO
    "RC0": "YAGEO",
    "RC-": "YAGEO",
    "AC0": "YAGEO",
    "CC0": "YAGEO",
    # Passives - Panasonic
    "ERJ": "Panasonic",
    # Passives - UNI-ROYAL
    "0201WM": "UNI-ROYAL",
    "0402WG": "UNI-ROYAL",
    "NQ01WM": "UNI-ROYAL",
    # Passives - Taiyo Yuden
    "TMK": "Taiyo Yuden",
    # Passives - FH (Fenghua)
    "0402B": "FH (Fenghua)",
    # TDK
    "DEA": "TDK",
    # MCUs
    "ESP32": "Espressif Systems",
    "RP2354": "Raspberry Pi",
    "RP2350": "Raspberry Pi",
    # RF
    "SX128": "Semtech",
    "RFX": "Qorvo",
    "2450AT": "Johanson Technology",
    # Sensors
    "LSM6": "STMicroelectronics",
    "LIS3": "STMicroelectronics",
    "BMP3": "Bosch Sensortec",
    # TI
    "LP59": "Texas Instruments",
    "LMR5": "Texas Instruments",
    "TPS2": "Texas Instruments",
    "TLV": "Texas Instruments",
    "SN74": "Texas Instruments",
    "TXU0": "Texas Instruments",
    # onsemi
    "NCV8": "onsemi",
    # Flash
    "W25Q": "Winbond",
    "BY25Q": "Boya Micro",
    # Diodes/ESD
    "DMN": "Diodes Incorporated",
    "SDM": "Diodes Incorporated",
    "AP21": "Diodes Incorporated",
    "RB161": "ROHM",
    "USBLC": "STMicroelectronics",
    # Connectors
    "SM06B": "JST",
    "SM08B": "JST",
    "U.FL": "Hirose",
    "BWU.FL": "BAT Wireless",
    "TYPE-C": "SHOU HAN",
    "TS2306": "SHOU HAN",
    # LEDs
    "XL-": "XINGLIGHT",
    "WS2812": "Worldsemi",
    # Inductors
    "AOTA": "Abracon",
    "XRTC": "XR",
    "MGFL": "Microgate",
    # LDO / Power
    "WL9": "WPMtek",
    "TPRT": "3PEAK",
    # Crystals/Oscillators
    "XTM": "TOGNJING",
    "SX0B": "Shenzhen SCTF",
    "OW7E": "YXC",
    # Mux
    "PI3A": "Diodes Incorporated",
}


def load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def guess_manufacturer(mpn: str, manufacturer_id: int | None = None) -> str:
    """Guess manufacturer from MPN prefix (preferred) or manufacturer_id."""
    # MPN prefix is more reliable than manufacturer_id
    for prefix in sorted(MPN_PREFIX_MAP.keys(), key=len, reverse=True):
        if mpn.upper().startswith(prefix.upper()):
            return MPN_PREFIX_MAP[prefix]
    # Fall back to manufacturer_id
    if manufacturer_id and manufacturer_id in MANUFACTURER_IDS:
        return MANUFACTURER_IDS[manufacturer_id]
    return "Unknown"


def lookup_lcsc(lcsc_code: str, cache: dict) -> dict | None:
    """Look up a part by LCSC code via jlcsearch API."""
    if lcsc_code in cache:
        return cache[lcsc_code]

    url = f"{API_BASE}?q={lcsc_code}&limit=1&full=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OpenFC-BOM-Tool/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  API error for {lcsc_code}: {e}")
        cache[lcsc_code] = None
        return None

    components = []
    if isinstance(data, dict):
        components = data.get("components", [])
    elif isinstance(data, list):
        components = data

    if not components:
        print(f"  No results for {lcsc_code}")
        cache[lcsc_code] = None
        return None

    comp = components[0]
    mpn = comp.get("mfr")
    manufacturer_id = comp.get("manufacturer_id")

    if not mpn:
        print(f"  No MPN found for {lcsc_code}")
        cache[lcsc_code] = None
        return None

    manufacturer = guess_manufacturer(mpn, manufacturer_id)
    result = {"mpn": mpn, "manufacturer": manufacturer}
    cache[lcsc_code] = result
    return result


def get_lcsc_code(sym) -> str | None:
    """Get LCSC part number from a symbol's properties."""
    for p in sym.property:
        if p.name in ("LCSC", "LCSC_Part") and p.value:
            val = p.value.strip()
            if val and val.startswith("C") and val[1:].isdigit():
                return val
    return None


def has_property(sym, name: str) -> bool:
    for p in sym.property:
        if p.name == name:
            return True
    return False


def add_property(sym, name: str, value: str):
    """Add a new property to a symbol via raw tree manipulation."""
    at_pos = [Symbol("at"), 0, 0, 0]
    effects = [
        Symbol("effects"),
        [Symbol("font"), [Symbol("size"), 1.27, 1.27]],
        [Symbol("hide"), Symbol("yes")],
    ]
    new_prop = [Symbol("property"), name, value, copy.deepcopy(at_pos), copy.deepcopy(effects)]

    raw = sym.raw
    last_prop_idx = 0
    for i, item in enumerate(raw):
        if isinstance(item, list) and len(item) > 0 and item[0] == Symbol("property"):
            last_prop_idx = i
    raw.insert(last_prop_idx + 1, new_prop)


def process_schematic(sch_path: str, cache: dict, write: bool, skip_api: bool) -> tuple[int, int]:
    s = Schematic(sch_path)
    modified = 0
    skipped = 0
    filename = os.path.basename(sch_path)

    for sym in s.symbol:
        ref = sym.property.Reference.value if hasattr(sym.property, "Reference") else ""
        if not ref or ref.startswith("#"):
            continue

        lcsc = get_lcsc_code(sym)
        if not lcsc:
            continue

        if has_property(sym, "MPN"):
            continue

        if skip_api and lcsc not in cache:
            skipped += 1
            continue

        if not skip_api and lcsc not in cache:
            info = lookup_lcsc(lcsc, cache)
            time.sleep(API_DELAY)
        else:
            info = cache.get(lcsc)

        if not info:
            skipped += 1
            continue

        mpn = info["mpn"]
        manufacturer = info["manufacturer"]

        add_property(sym, "MPN", mpn)
        if not has_property(sym, "Manufacturer"):
            add_property(sym, "Manufacturer", manufacturer)

        val = sym.property.Value.value if hasattr(sym.property, "Value") else ""
        print(f"  {filename}: {ref} ({val}) -> MPN={mpn}, Mfr={manufacturer}")
        modified += 1

    if write and modified > 0:
        s.write(sch_path)
        print(f"  Wrote {sch_path}")

    return modified, skipped


def main():
    parser = argparse.ArgumentParser(description="Add MPN/Manufacturer fields to KiCad schematics")
    parser.add_argument("--write", action="store_true", help="Write changes (default is dry-run)")
    parser.add_argument("--cache-only", action="store_true", help="Only build API cache, don't modify files")
    parser.add_argument("--skip-api", action="store_true", help="Only use cached data, no API calls")
    args = parser.parse_args()

    # Sheets referenced from root OpenFC.kicad_sch (exclude stale orphans)
    ACTIVE_SHEETS = {
        "OpenFC.kicad_sch", "rp2350a.kicad_sch", "elrs.kicad_sch",
        "power.kicad_sch", "imu.kicad_sch", "baro.kicad_sch",
        "blackbox.kicad_sch", "osd.kicad_sch", "leds.kicad_sch",
        "pads.kicad_sch", "compass.kicad_sch",
    }

    all_sch = sorted(glob.glob(str(HARDWARE_DIR / "*.kicad_sch")))
    sch_files = [f for f in all_sch if os.path.basename(f) in ACTIVE_SHEETS]
    skipped_sheets = [os.path.basename(f) for f in all_sch if os.path.basename(f) not in ACTIVE_SHEETS]
    if not sch_files:
        print("No active .kicad_sch files found in", HARDWARE_DIR)
        sys.exit(1)

    print(f"Found {len(sch_files)} active schematic files")
    if skipped_sheets:
        print(f"Skipping stale sheets: {', '.join(skipped_sheets)}")
    if not args.write and not args.cache_only:
        print("DRY RUN - use --write to save changes")

    cache = load_cache()
    initial_cache_size = len(cache)

    if args.cache_only:
        all_lcsc = set()
        for f in sch_files:
            s = Schematic(f)
            for sym in s.symbol:
                lcsc = get_lcsc_code(sym)
                if lcsc:
                    all_lcsc.add(lcsc)

        print(f"Found {len(all_lcsc)} unique LCSC parts, {len(cache)} already cached")
        for lcsc in sorted(all_lcsc):
            if lcsc not in cache:
                print(f"  Looking up {lcsc}...")
                lookup_lcsc(lcsc, cache)
                time.sleep(API_DELAY)

        save_cache(cache)
        print(f"Cache now has {len(cache)} entries (was {initial_cache_size})")
        return

    total_modified = 0
    total_skipped = 0

    for f in sch_files:
        print(f"\nProcessing {os.path.basename(f)}...")
        modified, skipped = process_schematic(f, cache, args.write, args.skip_api)
        total_modified += modified
        total_skipped += skipped

    save_cache(cache)

    print(f"\n{'WROTE' if args.write else 'Would modify'} {total_modified} symbols")
    if total_skipped:
        print(f"Skipped {total_skipped} symbols (no MPN data)")
    print(f"Cache: {len(cache)} entries (was {initial_cache_size})")


if __name__ == "__main__":
    main()

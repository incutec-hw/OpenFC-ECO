#!/usr/bin/env python3
"""
OpenFC-Lite Design Audit.

Parses the KiCad 9 design using kicad-skip (schematics) and pcbnew (PCB netlist)
and produces a comprehensive hardware inventory + Betaflight MFG validation report.

Run with KiCad's bundled Python so pcbnew is available:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
    hardware/tools/audit_design.py
"""

from __future__ import annotations

import collections
import os
import re
import sys
from pathlib import Path

HW = Path(__file__).resolve().parents[1]
ROOT_SCH = HW / "OpenFC.kicad_sch"
PCB = HW / "OpenFC.kicad_pcb"
OUT = HW / "tools" / "design_audit.md"

# ---------- Parsers ----------

# kicad-skip: path setup for user-level install
sys.path.insert(0, "/Users/stan/Library/Python/3.13/lib/python/site-packages")
try:
    from skip import Schematic
except ImportError:
    print("ERROR: kicad-skip not available. pip install kicad-skip", file=sys.stderr)
    sys.exit(1)

try:
    import pcbnew  # type: ignore
except ImportError:
    print("ERROR: pcbnew not on path. Run with KiCad bundled Python.", file=sys.stderr)
    sys.exit(1)


# ---------- Schematic walk ----------

def list_sheets(root_sch: Path):
    """Return list of (sheetname, sheetfile) pairs referenced from root."""
    s = Schematic(str(root_sch))
    out = []
    for sh in s.sheet:
        props = {p.name: p.value for p in sh.property}
        out.append((props.get("Sheetname", "?"), props.get("Sheetfile", "?")))
    return out


def collect_symbols(sch_path: Path):
    """Parse a schematic; return list of dicts per placed symbol."""
    try:
        s = Schematic(str(sch_path))
    except Exception as e:
        print(f"  WARN: cannot parse {sch_path.name}: {e}", file=sys.stderr)
        return []
    out = []
    for sym in s.symbol:
        try:
            lib_id = sym.lib_id.value
        except Exception:
            continue
        props = {p.name: p.value for p in sym.property}
        ref = props.get("Reference", "?")
        if ref.startswith("#"):
            continue  # power flag / gnd
        # Filter out stray power-flag symbols mis-refed in sub-sheets (e.g. blackbox
        # sub-sheet has U1..U9 that are actually +3.3V / GND power symbols).
        lib_id_lower = lib_id.lower()
        if lib_id_lower.startswith("power:") or lib_id_lower == "power":
            continue
        out.append({
            "sheet": sch_path.stem,
            "ref": ref,
            "value": props.get("Value", ""),
            "footprint": props.get("Footprint", ""),
            "mpn": props.get("MPN", ""),
            "lcsc": props.get("LCSC_Part", "") or props.get("LCSC", ""),
            "mfr": props.get("Manufacturer", ""),
            "description": props.get("Description", ""),
            "lib_id": lib_id,
            "dnp": bool(getattr(sym, "dnp", None) and sym.dnp.value),
            "on_board": bool(getattr(sym, "on_board", None) and sym.on_board.value),
        })
    return out


# ---------- PCB walk ----------

def load_pcb(pcb_path: Path):
    return pcbnew.LoadBoard(str(pcb_path))


def footprint_index(board):
    """ref -> {pads: {pad_num: netname}, funcs: {pad_num: pinfunc}, ...}"""
    idx = {}
    for fp in board.GetFootprints():
        r = fp.GetReference()
        pads = {}
        funcs = {}
        for pad in fp.Pads():
            num = pad.GetNumber()
            pads[num] = pad.GetNetname() or ""
            try:
                funcs[num] = pad.GetPinFunction() or ""
            except Exception:
                funcs[num] = ""
        idx[r] = {
            "value": fp.GetValue(),
            "footprint": fp.GetFPID().GetLibItemName().c_str() if hasattr(fp.GetFPID(), "GetLibItemName") else "",
            "pads": pads,
            "funcs": funcs,
        }
    return idx


def net_to_refpins(board):
    """netname -> list of (ref, pad_num, pad_name/function)"""
    d = collections.defaultdict(list)
    for fp in board.GetFootprints():
        r = fp.GetReference()
        for pad in fp.Pads():
            name = pad.GetNetname() or ""
            d[name].append((r, pad.GetNumber(), pad.GetPinFunction() if hasattr(pad, "GetPinFunction") else ""))
    return d


# ---------- Classification ----------

FUNC_RULES = [
    ("MCU",       lambda s: s["ref"].startswith("U") and "RP235" in s["value"].upper()),
    ("IMU",       lambda s: "LSM6" in s["value"].upper() or "ICM-4" in s["value"].upper() or "MPU6" in s["value"].upper()),
    ("Buck",      lambda s: s["ref"].startswith("U") and "LMR5" in s["value"].upper()),
    ("LDO",       lambda s: s["ref"].startswith("U") and ("LP5912" in s["value"].upper() or "NCV8187" in s["value"].upper())),
    ("Power Mux", lambda s: "TPS2116" in s["value"].upper()),
    ("OSD",       lambda s: "TLV3201" in s["value"].upper() or "TLV9061" in s["value"].upper() or "LVC1G3157" in s["value"].upper() or "PI3A223" in s["value"].upper()),
    ("SD card",   lambda s: "TF-" in s["value"].upper() or "SD" == s["ref"][:2].upper() and "CARD" in s["description"].upper()),
    ("USB",       lambda s: s["ref"].startswith("USB") or "USB" in s["value"].upper() and s["ref"].startswith("J") or s["ref"] == "USB1"),
    ("Switch",    lambda s: s["ref"].startswith("SW") or "TS2306" in s["value"].upper()),
    ("Connector", lambda s: s["ref"].startswith("J") or "CONN" in s["lib_id"].upper()),
    ("Test Pad",  lambda s: s["ref"].startswith("TP")),
    ("MOSFET",    lambda s: s["ref"].startswith("Q")),
    ("Diode/LED", lambda s: s["ref"].startswith("D") and ("LED" in s["value"].upper() or "LED" in s["description"].upper())),
    ("Diode",     lambda s: s["ref"].startswith("D")),
    ("Inductor",  lambda s: s["ref"].startswith("L")),
    ("Ferrite",   lambda s: s["ref"].startswith("FB")),
    ("Resistor",  lambda s: s["ref"].startswith("R")),
    ("Capacitor", lambda s: s["ref"].startswith("C")),
    ("IC",        lambda s: s["ref"].startswith("U")),
]

def classify(sym):
    for name, fn in FUNC_RULES:
        try:
            if fn(sym):
                return name
        except Exception:
            continue
    return "Misc"


# ---------- Report builders ----------

def refs_on_net(net2rp, netname, exclude_refs=None):
    exclude_refs = set(exclude_refs or [])
    return [(r, n, f) for (r, n, f) in net2rp.get(netname, []) if r not in exclude_refs]


def find_caps_between(syms_by_ref, net2rp, netname_a, netname_b="GND"):
    """Return list of cap refs having one pad on netname_a and other on netname_b."""
    caps_on_a = {r for (r, _, _) in net2rp.get(netname_a, []) if r.startswith("C")}
    caps_on_b = {r for (r, _, _) in net2rp.get(netname_b, []) if r.startswith("C")}
    return sorted(caps_on_a & caps_on_b, key=lambda x: int(re.sub(r"\D", "", x) or 0))


def find_nets_matching(net2rp, *patterns):
    pats = [re.compile(p, re.I) for p in patterns]
    return [n for n in net2rp if any(p.search(n) for p in pats)]


def pad_net(fp_idx, ref, pad_num):
    return fp_idx.get(ref, {}).get("pads", {}).get(str(pad_num), "")


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)


# ---------- Main audit ----------

def main():
    lines = []
    W = lines.append

    W("# OpenFC-Lite Design Audit\n")
    W(f"Generated from `{ROOT_SCH.name}` + `{PCB.name}` via kicad-skip + pcbnew.\n")

    # ---- 1. Hierarchy ----
    W("## 1. Top-level Hierarchy\n")
    sheets = list_sheets(ROOT_SCH)
    rows = []
    for name, path in sheets:
        exists = (HW / path).exists()
        rows.append([name, f"`{path}`", "yes" if exists else "**MISSING**"])
    W(md_table(["Sheetname", "File", "On disk"], rows))
    W("")
    W(f"Root schematic: `{ROOT_SCH.name}` — {len(sheets)} sub-sheet(s) referenced.\n")

    # ---- 2. Components ----
    W("## 2. Component Inventory\n")
    all_syms = []
    for name, path in sheets:
        p = HW / path
        if p.exists():
            all_syms.extend(collect_symbols(p))
    # Deduplicate by ref (symbols may appear in multiple places due to power/gnd)
    seen = {}
    for s in all_syms:
        seen.setdefault(s["ref"], s)
    syms = list(seen.values())

    W(f"Total placed refs: **{len(syms)}** (DNP excluded: "
      f"{len([s for s in syms if s['dnp']])}).\n")

    by_func = collections.defaultdict(list)
    for s in syms:
        by_func[classify(s)].append(s)

    # Print ICs, regulators, connectors etc fully; print caps/resistors summarized
    DETAIL_FUNCS = ["MCU", "IMU", "Buck", "LDO", "Power Mux", "OSD",
                    "SD card", "USB", "Switch", "MOSFET",
                    "Diode/LED", "Diode", "IC", "Inductor", "Ferrite"]
    def ref_sort_key(ref):
        m = re.match(r"([A-Za-z]+)(\d+)", ref)
        if m:
            return (m.group(1), int(m.group(2)))
        return (ref, 0)

    for fn in DETAIL_FUNCS:
        items = sorted(by_func.get(fn, []), key=lambda x: ref_sort_key(x["ref"]))
        if not items:
            continue
        W(f"### {fn} ({len(items)})\n")
        rows = []
        for s in items:
            mpn = s["mpn"] or s["value"]
            dnp = " DNP" if s["dnp"] else ""
            rows.append([s["ref"] + dnp, s["value"], mpn, s["lcsc"] or "-",
                         s["mfr"] or "-", s["footprint"].split(":")[-1] if s["footprint"] else "-",
                         s["sheet"]])
        W(md_table(["Ref", "Value", "MPN", "LCSC", "Mfr", "Footprint", "Sheet"], rows))
        W("")
    # Connector summary only (detail in section 14)
    conns = by_func.get("Connector", [])
    if conns:
        W(f"### Connector / Solder Pads ({len(conns)})\n")
        W("(full net list in section 14)\n")
        # group by footprint
        fp_count = collections.Counter((s["footprint"].split(":")[-1] or "-", s["sheet"]) for s in conns)
        rows = [[fp, sh, c] for (fp, sh), c in sorted(fp_count.items())]
        W(md_table(["Footprint", "Sheet", "Count"], rows))
        W("")

    # Passives summary
    W("### Passives summary\n")
    rows = []
    for fn in ("Resistor", "Capacitor", "Test Pad"):
        items = [s for s in by_func.get(fn, []) if not s["dnp"]]
        dnp = [s for s in by_func.get(fn, []) if s["dnp"]]
        rows.append([fn, len(items), len(dnp)])
    W(md_table(["Function", "Placed", "DNP"], rows))
    W("")

    # ---- Load PCB for net-level analysis ----
    board = load_pcb(PCB)
    fp_idx = footprint_index(board)
    net2rp = net_to_refpins(board)

    # ---- 3. Power tree ----
    W("## 3. Power Tree\n")
    W("```")
    W("+BATT -> U6 (LMR51420YFDDCR buck) -> +12V   [switchable via GPIO11 via Q?]")
    W("+BATT -> U7 (LMR51420YFDDCR buck) -> +5V_BUCK")
    W("+5V_BUCK -+")
    W("          +- U33 (TPS2116 mux) -> +5V")
    W("VBUS(USB)-+")
    W("+5V -> U13 (LP5912-3.3) -> +3.3V")
    W("+3.3V -> U36 (RP2354B VREG) -> +1.1V_CORE (DVDD)")
    W("+5V -> U21 (NCV8187 LDO) -> +1.8V_GYRO")
    W("```\n")

    regs = [
        ("U6",  "LMR51420YFDDCR", "12V buck"),
        ("U7",  "LMR51420YFDDCR", "5V buck"),
        ("U13", "LP5912-3.3DRVR", "3.3V LDO"),
        ("U21", "NCV8187AMT180TAG", "1.8V gyro LDO"),
        ("U33", "TPS2116DRLR", "5V power mux"),
    ]
    rows = []
    for ref, mpn, role in regs:
        fp = fp_idx.get(ref, {})
        pads = fp.get("pads", {})
        # summarise input / EN / output if we can infer by pin function from schematic
        # Just print key pads
        rows.append([ref, role, mpn, fp.get("footprint", "-"),
                     "; ".join(f"{k}→{v}" for k, v in sorted(pads.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 99))])
    W(md_table(["Ref", "Role", "MPN", "Footprint", "Pad → Net"], rows))
    W("")

    # ---- 4. Bypass caps per rail ----
    W("## 4. Bypass caps per power rail\n")
    rails = ["+BATT", "+12V", "+5V_BUCK", "+5V", "VBUS", "+3.3V", "+1.8V_GYRO",
             "+1.1V", "+1.1V_CORE", "DVDD"]
    rows = []
    for rail in rails:
        # try exact, then with leading /
        candidates = [rail, "/" + rail, rail.lstrip("+"), "/" + rail.lstrip("+")]
        found_net = None
        for c in candidates:
            if c in net2rp:
                found_net = c
                break
        if not found_net:
            # try loose match
            loose = [n for n in net2rp if n.strip("/+").upper() == rail.strip("/+").upper()]
            if loose:
                found_net = loose[0]
        if not found_net:
            rows.append([rail, "— (net not found)", "-", "-"])
            continue
        caps = find_caps_between({}, net2rp, found_net, "GND")
        # count how many pins are on this net (fanout size)
        fanout = len(net2rp.get(found_net, []))
        rows.append([rail, found_net, len(caps), ", ".join(caps) if caps else "—"])
    W(md_table(["Rail", "Net", "# Caps to GND", "Cap refs"], rows))
    W("")
    # Also report ALL nets that look like rails
    rail_like = [n for n in net2rp if re.search(r"(^|/)(\+?\d+V|VBUS|VBAT|VDD|AVDD|DVDD|VREG)", n, re.I)]
    W("Rail-like nets present:\n")
    W(", ".join(f"`{n}`" for n in sorted(set(rail_like))))
    W("")

    # ---- 5. ADC inputs ----
    W("## 5. ADC Inputs\n")
    adc_nets = {
        "VBAT_SENSE": ["VBAT", "VBATT_SENSE", "VBAT_ADC", "BATT_ADC", "VBAT_SCALE", "BATTERY_ADC"],
        "CURR_SENSE": ["CURRENT", "I_SENSE", "CURR_ADC", "CURR_SENSE", "IMON", "CURRENT_ADC"],
        "RSSI":       ["RSSI", "RSSI_ADC"],
        "EXT":        ["EXT_ADC", "ADC_EXT", "EXT"],
    }
    # Try to find the MCU's actual ADC pins: GPIO40,41,45,47 per CLAUDE.md
    mcu_ref = "U36"
    mcu_fp = fp_idx.get(mcu_ref, {})
    # The ADC nets go to MCU pins — find them by following net back to U36
    rows = []
    for role, candidates in adc_nets.items():
        net = None
        for c in candidates:
            match = [n for n in net2rp if c.upper() in n.upper()]
            if match:
                net = sorted(match, key=len)[0]
                break
        if not net:
            rows.append([role, "— not found", "-", "-", "-"])
            continue
        # Find MCU pad carrying this net
        mcu_pad = "-"
        for p, n in mcu_fp.get("pads", {}).items():
            if n == net:
                mcu_pad = p
                break
        # Find resistors on the net
        res = [r for (r, _, _) in net2rp.get(net, []) if r.startswith("R")]
        caps = find_caps_between({}, net2rp, net, "GND")
        rows.append([role, net, mcu_pad,
                     ", ".join(sorted(set(res))) or "—",
                     ", ".join(caps) or "**NONE**"])
    W(md_table(["Role", "Net", "MCU pad", "Resistors on net", "Bypass caps to GND"], rows))
    W("")
    W("**Check**: A CURRENT-sense ADC input WITHOUT a bypass cap at the MCU pin is a "
      "Betaflight MFG-guideline violation (noise couples straight into ADC).\n")

    # ---- 6. SPI buses & CS pull-ups ----
    W("## 6. SPI Buses & CS pull-ups\n")
    spi_nets = {
        "SPI0 SCK":  [n for n in net2rp if re.search(r"SPI0?_?SCK|GYRO_?SCK|IMU_?SCK", n, re.I)],
        "SPI0 MOSI": [n for n in net2rp if re.search(r"SPI0?_?(MOSI|SDI|SDA)|GYRO_?MOSI|IMU_?MOSI", n, re.I)],
        "SPI0 MISO": [n for n in net2rp if re.search(r"SPI0?_?(MISO|SDO)|GYRO_?MISO|IMU_?MISO", n, re.I)],
        "IMU CS":    [n for n in net2rp if re.search(r"(IMU|GYRO).*CS|CS_?(IMU|GYRO)", n, re.I)],
        "SD CS":     [n for n in net2rp if re.search(r"SD.*CS|CS_?SD|BB_?CS", n, re.I)],
        "SD MOSI":   [n for n in net2rp if re.search(r"SD.*MOSI|SD.*DI|SD_?CMD", n, re.I)],
        "SD MISO":   [n for n in net2rp if re.search(r"SD.*MISO|SD.*DO|SD_?DAT0?", n, re.I)],
        "SD SCK":    [n for n in net2rp if re.search(r"SD.*SCK|SD.*CLK", n, re.I)],
    }
    rows = []
    for role, nets in spi_nets.items():
        if not nets:
            rows.append([role, "—", "-", "-"])
            continue
        net = nets[0]
        # list refs on that net
        refs = sorted(set(r for (r, _, _) in net2rp[net]))
        # resistors on net (pull-up candidates)
        rs = [r for r in refs if r.startswith("R")]
        rows.append([role, net, ", ".join(refs), ", ".join(rs) or "—"])
    W(md_table(["Signal", "Net", "Refs on net", "Resistors (pull-ups?)"], rows))
    W("")

    # Specific checks for CS pull-ups
    W("### CS pull-up check (to +3.3V)\n")
    cs_checks = []

    def find_cs_pad(ref):
        """Return (pad_num, netname) for the CS pin of a footprint, using pin function."""
        fp = fp_idx.get(ref, {})
        for p, func in fp.get("funcs", {}).items():
            if re.search(r"(^|_)CS(_|$)", func or "", re.I):
                return p, fp.get("pads", {}).get(p, "")
        return None, None

    # IMU CS -> U14 using pin function
    pad, net = find_cs_pad("U14")
    cs_checks.append((f"IMU_CS (U14 pad {pad})", net))
    # SD CS -> Card2 pad 2 (TF-021B-H265 pinout: pin2=CS/DAT3)
    for ref, fp in fp_idx.items():
        v = fp.get("value", "").upper()
        if "TF-" in v or "MICROSD" in v:
            # TF socket pad 2 = CS in SPI mode
            n = fp.get("pads", {}).get("2", "")
            cs_checks.append((f"SD_CS ({ref} pad 2)", n))
            break
    rows = []
    for role, net in cs_checks:
        if not net:
            rows.append([role, "—", "—", "—"])
            continue
        rs = [r for (r, _, _) in net2rp.get(net, []) if r.startswith("R")]
        # Does any of those R's touch +3.3V or +3V3?
        has_pullup = False
        pu_ref = "-"
        for rref in rs:
            rpads = fp_idx.get(rref, {}).get("pads", {})
            other_nets = set(rpads.values()) - {net}
            if any(re.search(r"3V3|3\.3V|VDDIO", x, re.I) for x in other_nets):
                has_pullup = True
                pu_ref = rref
                break
        rows.append([role, net, "YES" if has_pullup else "NO", pu_ref])
    W(md_table(["CS line", "Net", "Pull-up present?", "Pull-up ref"], rows))
    W("")

    # ---- 7. Status LEDs ----
    W("## 7. Status LEDs (non-WS2812)\n")
    leds = [s for s in syms if s["ref"].startswith("D") and
            ("LED" in s["value"].upper() or "LED" in (s["description"] or "").upper())]
    rows = []
    for led in sorted(leds, key=lambda x: x["ref"]):
        ref = led["ref"]
        fp = fp_idx.get(ref, {})
        pads = fp.get("pads", {})
        # LEDs usually have A/K or 1/2
        pin_nets = ", ".join(f"{k}→{v}" for k, v in pads.items())
        # Try to identify MCU pin driving it (non-rail end)
        drivers = [v for v in pads.values() if not re.search(r"\+?(\d+V|GND|VBUS|VBAT)", v, re.I)]
        rows.append([ref, led["value"], led["mpn"] or "-", pin_nets, ", ".join(drivers) or "—"])
    W(md_table(["Ref", "Value/Color", "MPN", "Pad nets", "Likely MCU-side net"], rows))
    W("")
    # Blue LED check
    blue = [l for l in leds if "BLUE" in l["value"].upper() or "BLU" in l["value"].upper()]
    W(f"Blue LED (Betaflight LED0 requirement): **{'PRESENT' if blue else 'MISSING'}** "
      f"({', '.join(l['ref'] for l in blue) or 'none'})\n")

    # ---- 8. I2C ----
    W("## 8. I2C Pull-ups\n")
    sda_net = [n for n in net2rp if re.search(r"I2C.*SDA|SDA$|/SDA", n, re.I)]
    scl_net = [n for n in net2rp if re.search(r"I2C.*SCL|SCL$|/SCL", n, re.I)]
    rows = []
    for role, nets in (("I2C_SDA", sda_net), ("I2C_SCL", scl_net)):
        if not nets:
            rows.append([role, "—", "-", "-"])
            continue
        net = nets[0]
        refs = sorted(set(r for (r, _, _) in net2rp[net]))
        rs = [r for r in refs if r.startswith("R")]
        has_pullup = False
        for rref in rs:
            rpads = fp_idx.get(rref, {}).get("pads", {})
            if any(re.search(r"3V3|3\.3V|VDDIO", x, re.I) for x in rpads.values()):
                has_pullup = True
                break
        rows.append([role, net, ", ".join(refs), "YES" if has_pullup else "**NO**"])
    W(md_table(["Signal", "Net", "Refs on net", "Pull-up to 3.3V"], rows))
    W("")

    # ---- 9. MCU pinout ----
    W("## 9. RP2354B (U36) Pinout\n")
    mcu_fp = fp_idx.get("U36", {})
    pads = mcu_fp.get("pads", {})
    rows = []
    for p in sorted(pads.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        n = pads[p]
        # skip internal / power pads for clarity (keep but mark)
        rows.append([p, n])
    W(md_table(["Pad", "Net"], rows))
    W("")

    # ---- 10. OSD circuit ----
    W("## 10. OSD Circuit\n")
    osd_refs = [s["ref"] for s in syms if s["ref"] in ("U34", "U35", "U38")]
    rows = []
    for ref in osd_refs:
        fp = fp_idx.get(ref, {})
        rows.append([ref, fp.get("value"), fp.get("footprint"),
                     "; ".join(f"{k}→{v}" for k, v in fp.get("pads", {}).items())])
    W(md_table(["Ref", "Value", "Footprint", "Pad → Net"], rows))
    W("")

    # ---- 11. SD card ----
    W("## 11. SD Card (Blackbox)\n")
    sd_refs = [s for s in syms if
               "TF-" in s["value"].upper() or "MICROSD" in s["value"].upper() or
               "SD_CARD" in s["value"].upper() or "CARD" in s["description"].upper()]
    if not sd_refs:
        # look in pcb fps too
        for ref, fp in fp_idx.items():
            if "TF-" in fp.get("value", "").upper():
                sd_refs.append({"ref": ref, "value": fp["value"], "description": "", "lib_id": "",
                                "mpn": "", "lcsc": "", "footprint": fp.get("footprint", ""),
                                "mfr": "", "sheet": "", "dnp": False, "on_board": True})
    rows = []
    for s in sd_refs:
        ref = s["ref"]
        fp = fp_idx.get(ref, {})
        pads = fp.get("pads", {})
        rows.append([ref, s["value"], fp.get("footprint"),
                     "; ".join(f"{k}→{v}" for k, v in pads.items())])
    W(md_table(["Ref", "Value", "Footprint", "Pad → Net"], rows))
    W("")

    # ---- 12. Motor outputs ----
    W("## 12. Motor Outputs (M1-M4)\n")
    motor_nets = []
    for k in ["M1", "M2", "M3", "M4", "MOTOR1", "MOTOR2", "MOTOR3", "MOTOR4"]:
        motor_nets.extend([n for n in net2rp if re.search(r"(^|/)" + k + "$", n, re.I)])
    motor_nets = sorted(set(motor_nets))
    rows = []
    for mn in motor_nets:
        refs = sorted(set(r for (r, _, _) in net2rp[mn]))
        rows.append([mn, ", ".join(refs)])
    W(md_table(["Motor net", "Refs on net"], rows))
    W("")

    # ---- 13. Reset / Boot ----
    W("## 13. Reset / Boot\n")
    # RP2350 has RUN and BOOTSEL. SWD/DBG pins too.
    for pname in ["RUN", "BOOTSEL", "NRST", "USB_BOOT"]:
        matches = [n for n in net2rp if pname in n.upper()]
        if matches:
            for m in matches:
                refs = sorted(set(r for (r, _, _) in net2rp[m]))
                W(f"- **{pname}**: net `{m}` — refs: {', '.join(refs)}")
    # Look at U36 pad for RUN
    # Check if RUN net has a pull-up / button
    for pad, net in mcu_fp.get("pads", {}).items():
        if "RUN" in net.upper():
            refs_on = sorted(set(r for (r, _, _) in net2rp[net]))
            W(f"- U36 pad {pad} (RUN) connects to `{net}`; refs on net: {', '.join(refs_on)}")
    W("")

    # ---- 14. Connectors / pads ----
    W("## 14. Connectors & Pads\n")
    conn_items = sorted(
        [s for s in syms if s["ref"].startswith("J") or s["ref"].startswith("USB") or s["ref"].startswith("TP")],
        key=lambda x: (x["ref"][0], int(re.sub(r"\D", "", x["ref"]) or 0))
    )
    groups = collections.defaultdict(list)
    for s in conn_items:
        if s["ref"].startswith("TP"):
            groups["Test Pads"].append(s)
        elif s["ref"].startswith("USB"):
            groups["USB"].append(s)
        else:
            groups["Solder Pads / Connectors"].append(s)
    for g, items in groups.items():
        W(f"### {g}\n")
        rows = []
        for s in items:
            fp = fp_idx.get(s["ref"], {})
            pads_map = fp.get("pads", {})
            nets_csv = "; ".join(f"p{k}→{v}" for k, v in sorted(pads_map.items(),
                                                                 key=lambda x: int(x[0]) if x[0].isdigit() else 99))
            # If single-pad pad, list just the net
            if len(pads_map) == 1:
                only_net = next(iter(pads_map.values()))
                nets_csv = only_net
            fpname = (fp.get("footprint") or "-").split(":")[-1]
            rows.append([s["ref"], fpname, nets_csv])
        W(md_table(["Ref", "Footprint", "Pad → Net"], rows))
        W("")

    # ---- Cross-check GPIO map ----
    W("## 15. CLAUDE.md GPIO map cross-check\n")
    # From CLAUDE.md
    claude_gpio = {
        "GPIO0":  "UART0 TX",
        "GPIO1":  "UART0 RX",
        "GPIO2":  "PIO UART0 TX",
        "GPIO3":  "PIO UART0 RX",
        "GPIO6":  "Beeper",
        "GPIO11": "10V enable",
        "GPIO12": "Status LED",
        "GPIO13": "IMU INT",
        "GPIO14": "IMU CS",
        "GPIO18": "IMU SCK",
        "GPIO19": "IMU MISO",
        "GPIO20": "IMU MOSI",
        "GPIO21": "UART1 RX",
        "GPIO22": "UART1 TX",
        "GPIO23": "LED strip",
        "GPIO26": "PIO UART1 TX",
        "GPIO27": "PIO UART1 RX",
        "GPIO28": "M4",
        "GPIO29": "M3",
        "GPIO30": "M2",
        "GPIO31": "M1",
        "GPIO32": "OSD VBLACK",
        "GPIO33": "OSD SYNC_IN",
        "GPIO34": "OSD PIXEL_SEL",
        "GPIO35": "OSD VWHITE",
        "GPIO36": "OSD COLOR_SEL",
        "GPIO37": "OSD SYNCLVL",
        "GPIO40": "CURRENT ADC",
        "GPIO41": "VBAT ADC",
        "GPIO45": "RSSI ADC",
        "GPIO47": "EXT ADC",
    }
    # Build GPIO# -> (pad, net) map from U36 pin functions
    gpio_map = {}
    for pad, func in mcu_fp.get("funcs", {}).items():
        m = re.match(r"GPIO(\d+)", func or "", re.I)
        if m:
            gnum = int(m.group(1))
            gpio_map[gnum] = (pad, mcu_fp.get("pads", {}).get(pad, ""))
    rows = []
    for g, desc in sorted(claude_gpio.items(), key=lambda x: int(x[0][4:])):
        gnum = int(g[4:])
        pad_net = gpio_map.get(gnum)
        if pad_net:
            rows.append([g, desc, pad_net[0], pad_net[1]])
        else:
            rows.append([g, desc, "—", "— (GPIO not wired on MCU)"])
    W(md_table(["GPIO", "CLAUDE.md function", "U36 pad", "Net"], rows))
    W("")
    # And report GPIOs on MCU NOT in the CLAUDE.md table (stragglers)
    claude_nums = {int(g[4:]) for g in claude_gpio}
    extras = sorted(set(gpio_map.keys()) - claude_nums)
    if extras:
        W("GPIOs wired on MCU but not documented in CLAUDE.md:\n")
        rows = [[f"GPIO{n}", gpio_map[n][0], gpio_map[n][1]] for n in extras]
        W(md_table(["GPIO", "U36 pad", "Net"], rows))
        W("")

    # ---- 16. Summary table of open observations ----
    W("## 16. Audit findings\n")
    findings = []

    def has_pullup_to_3v3(net):
        if not net or net in ("GND", ""):
            return False
        rs = [r for (r, _, _) in net2rp.get(net, []) if r.startswith("R")]
        for rref in rs:
            pads_vals = fp_idx.get(rref, {}).get("pads", {}).values()
            if any(re.search(r"3V3|3\.3V|VDDIO|^\+3.3V", x, re.I) for x in pads_vals):
                return True
        return False

    # Current-sense cap check
    curr_candidates = [n for n in net2rp if re.search(r"CURRENT|I_?SENSE|CURR_?ADC|IMON", n, re.I)]
    if curr_candidates:
        cn = curr_candidates[0]
        caps = find_caps_between({}, net2rp, cn, "GND")
        if not caps:
            findings.append(("HIGH", f"CURRENT-sense net `{cn}` has NO bypass cap to GND — add ~100nF near MCU ADC pin."))
    # VBAT bypass
    vb_candidates = [n for n in net2rp if re.search(r"VBAT.*SENSE|VBAT_?ADC", n, re.I)]
    if vb_candidates:
        cn = vb_candidates[0]
        caps = find_caps_between({}, net2rp, cn, "GND")
        if not caps:
            findings.append(("MED", f"VBAT-sense net `{cn}` has NO bypass cap to GND."))
    # RSSI bypass
    rssi_candidates = [n for n in net2rp if re.search(r"(^|/)RSSI($|_ADC)", n, re.I)]
    if rssi_candidates:
        cn = rssi_candidates[0]
        caps = find_caps_between({}, net2rp, cn, "GND")
        if not caps:
            findings.append(("LOW", f"RSSI ADC net `{cn}` has no bypass cap to GND (acceptable for PWM/analog RSSI)."))
    # IMU CS pull-up (use pin function)
    imu_cs_pad_n, imu_cs_net = find_cs_pad("U14")
    if imu_cs_net and not has_pullup_to_3v3(imu_cs_net):
        findings.append(("HIGH", f"IMU CS net `{imu_cs_net}` (U14 pad {imu_cs_pad_n}) has NO pull-up to 3.3V — "
                                 "floating CS at boot can cause bus contention; add 10k to +3.3V."))
    # SD CS pull-up
    for ref, fp in fp_idx.items():
        v = fp.get("value", "").upper()
        if "TF-" in v or "MICROSD" in v:
            sd_cs_net = fp.get("pads", {}).get("2", "")
            if sd_cs_net and not has_pullup_to_3v3(sd_cs_net):
                # Check if a resistor is on the net at all (might be pull-down or series)
                rs = [r for (r, _, _) in net2rp.get(sd_cs_net, []) if r.startswith("R")]
                if not rs:
                    findings.append(("HIGH", f"SD CS net `{sd_cs_net}` has no pull-up to 3.3V — SD cards "
                                             "require CS idle-high or they stay in SD-mode."))
                else:
                    findings.append(("MED", f"SD CS net `{sd_cs_net}` has resistor(s) {rs} but none detected "
                                            "going to 3.3V — verify pull-up vs series resistor."))
            break
    # MCU reset (RUN) pull-up
    run_net = None
    for pad, func in mcu_fp.get("funcs", {}).items():
        if re.search(r"^RUN(_|$)", func or "", re.I):
            run_net = mcu_fp.get("pads", {}).get(pad, "")
            break
    if run_net and not has_pullup_to_3v3(run_net):
        findings.append(("HIGH", f"MCU RUN net `{run_net}` has NO pull-up to 3.3V — "
                                 "RP2350 datasheet requires external pull-up + cap on RUN."))
    # SD CS pull-up
    # LED blue
    if not [l for l in leds if "BLUE" in l["value"].upper()]:
        findings.append(("MED", "No explicit BLUE LED found for Betaflight LED0 status."))
    # Decoupling per MCU
    # Count caps on 3.3V near U36
    if findings:
        rows = [[sev, msg] for sev, msg in findings]
        W(md_table(["Severity", "Finding"], rows))
    else:
        W("No automated red flags detected.\n")
    W("")

    # Write file
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT}")
    print(f"Length: {OUT.stat().st_size} bytes, {len(lines)} lines")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.openfc_netlist_extract import ParseError, parse_sexpr, tokenize_sexpr  # type: ignore


@dataclass
class Pad:
    number: str
    net_name: str = ""
    net_id: Optional[str] = None
    pinfunction: str = ""
    pintype: str = ""


@dataclass
class Footprint:
    fp_id: str
    ref: str
    value: str
    properties: Dict[str, str]
    pads: List[Pad]


def _kv_str(node: Any) -> Optional[tuple[str, str]]:
    if isinstance(node, list) and len(node) >= 2 and isinstance(node[0], str) and isinstance(node[1], str):
        return node[0], node[1]
    return None


def _extract_property(node: Any) -> Optional[tuple[str, str]]:
    # (property "Reference" "U36" ...)
    if not (isinstance(node, list) and len(node) >= 3 and node[0] == "property"):
        return None
    name = node[1] if isinstance(node[1], str) else ""
    val = node[2] if isinstance(node[2], str) else ""
    if name:
        return name, val
    return None


def parse_board(board_path: Path) -> tuple[List[Footprint], Dict[str, str]]:
    text = board_path.read_text(encoding="utf-8", errors="replace")
    root = parse_sexpr(tokenize_sexpr(text))
    if not isinstance(root, list) or not root or root[0] != "kicad_pcb":
        raise ParseError("expected (kicad_pcb ...)")

    nets_by_id: Dict[str, str] = {}
    footprints: List[Footprint] = []

    for item in root[1:]:
        if not (isinstance(item, list) and item):
            continue
        if item[0] == "net":
            # (net 115 "/RP2350A/XIN")
            if len(item) >= 3 and isinstance(item[1], str) and isinstance(item[2], str):
                nets_by_id[item[1]] = item[2]
            continue

        if item[0] != "footprint":
            continue

        fp_id = item[1] if len(item) > 1 and isinstance(item[1], str) else ""
        props: Dict[str, str] = {}
        ref = ""
        value = ""
        pads: List[Pad] = []

        for sub in item[2:]:
            prop = _extract_property(sub)
            if prop:
                k, v = prop
                props[k] = v
                if k == "Reference":
                    ref = v
                elif k == "Value":
                    value = v
                continue

            if not (isinstance(sub, list) and sub):
                continue
            if sub[0] != "pad":
                continue
            # (pad "30" smd rect ... (net 115 "/RP2350A/XIN") (pinfunction "XIN") (pintype "unspecified") ...)
            pad_number = sub[1] if len(sub) > 1 and isinstance(sub[1], str) else ""
            pad = Pad(number=pad_number)
            for psub in sub[2:]:
                if not (isinstance(psub, list) and psub):
                    continue
                if psub[0] == "net":
                    # (net 115 "/RP2350A/XIN")
                    if len(psub) >= 3 and isinstance(psub[1], str) and isinstance(psub[2], str):
                        pad.net_id = psub[1]
                        pad.net_name = psub[2]
                elif psub[0] == "pinfunction" and len(psub) >= 2 and isinstance(psub[1], str):
                    pad.pinfunction = psub[1]
                elif psub[0] == "pintype" and len(psub) >= 2 and isinstance(psub[1], str):
                    pad.pintype = psub[1]
            pads.append(pad)

        if ref:
            footprints.append(Footprint(fp_id=fp_id, ref=ref, value=value, properties=props, pads=pads))

    return footprints, nets_by_id


def is_ic_ref(ref: str) -> bool:
    return bool(re.match(r"^U\d+$", ref))


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract per-footprint pad connectivity from OpenFC.kicad_pcb")
    ap.add_argument("--pcb", default="OpenFC.kicad_pcb", help="Path to KiCad PCB file")
    ap.add_argument("--outdir", default="analysis/pcb_extract", help="Output directory")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    fps, _nets_by_id = parse_board(Path(args.pcb))

    # Components table
    with (outdir / "footprints.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ref", "value", "fp_id", "LCSC"])
        for fp in sorted(fps, key=lambda x: x.ref):
            w.writerow([fp.ref, fp.value, fp.fp_id, fp.properties.get("LCSC", "")])

    # IC extraction with pad nets + pinfunctions
    ics: List[Dict[str, Any]] = []
    for fp in fps:
        if not is_ic_ref(fp.ref):
            continue
        pins: Dict[str, Dict[str, str]] = {}
        for pad in fp.pads:
            pins[pad.number] = {"net": pad.net_name, "pinfunction": pad.pinfunction, "pintype": pad.pintype}
        ics.append(
            {
                "ref": fp.ref,
                "value": fp.value,
                "fp_id": fp.fp_id,
                "lcsc": fp.properties.get("LCSC", ""),
                "pins": pins,
                "properties": fp.properties,
            }
        )
    ics.sort(key=lambda x: x["ref"])
    (outdir / "ics.json").write_text(json.dumps(ics, indent=2, sort_keys=True), encoding="utf-8")

    # Nets with pad counts (useful for spotting orphan nets)
    net_counts: Dict[str, int] = {}
    for fp in fps:
        for pad in fp.pads:
            if not pad.net_name:
                continue
            net_counts[pad.net_name] = net_counts.get(pad.net_name, 0) + 1
    (outdir / "net_counts.json").write_text(json.dumps(net_counts, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

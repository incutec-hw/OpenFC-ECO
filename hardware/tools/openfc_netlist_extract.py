#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


Token = str


def tokenize_sexpr(text: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch in ("(", ")"):
            tokens.append(ch)
            i += 1
            continue
        if ch == '"':
            i += 1
            buf: List[str] = []
            while i < n:
                ch2 = text[i]
                if ch2 == "\\":
                    if i + 1 < n:
                        buf.append(text[i + 1])
                        i += 2
                        continue
                if ch2 == '"':
                    i += 1
                    break
                buf.append(ch2)
                i += 1
            tokens.append("".join(buf))
            continue
        # symbol
        j = i
        while j < n and (not text[j].isspace()) and text[j] not in ("(", ")"):
            j += 1
        tokens.append(text[i:j])
        i = j
    return tokens


class ParseError(RuntimeError):
    pass


def parse_sexpr(tokens: List[Token]) -> Any:
    i = 0

    def parse_one() -> Any:
        nonlocal i
        if i >= len(tokens):
            raise ParseError("unexpected end of tokens")
        tok = tokens[i]
        if tok == "(":
            i += 1
            lst: List[Any] = []
            while True:
                if i >= len(tokens):
                    raise ParseError("unterminated list")
                if tokens[i] == ")":
                    i += 1
                    return lst
                lst.append(parse_one())
        if tok == ")":
            raise ParseError("unexpected ')'")
        i += 1
        return tok

    expr = parse_one()
    if i != len(tokens):
        raise ParseError(f"trailing tokens at {i}/{len(tokens)}")
    return expr


def _kv(node: Any) -> Optional[Tuple[str, str]]:
    if isinstance(node, list) and len(node) == 2 and isinstance(node[0], str) and isinstance(node[1], str):
        return node[0], node[1]
    return None


def _find_sections(root: Any) -> Dict[str, Any]:
    sections: Dict[str, Any] = {}
    if not isinstance(root, list) or not root or root[0] != "export":
        raise ParseError("expected (export ...)")
    for item in root[1:]:
        if isinstance(item, list) and item:
            key = item[0]
            if isinstance(key, str) and key not in sections:
                sections[key] = item
    return sections


@dataclass
class Component:
    ref: str
    value: str = ""
    footprint: str = ""
    datasheet: str = ""
    description: str = ""
    sheetname: str = ""
    sheetfile: str = ""
    properties: Dict[str, str] = None  # type: ignore[assignment]
    fields: Dict[str, str] = None  # type: ignore[assignment]
    lib: str = ""
    part: str = ""
    connections: Dict[str, str] = None  # type: ignore[assignment]
    pinfunctions: Dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.properties is None:
            self.properties = {}
        if self.fields is None:
            self.fields = {}
        if self.connections is None:
            self.connections = {}
        if self.pinfunctions is None:
            self.pinfunctions = {}


def parse_components(components_section: Any) -> Dict[str, Component]:
    comps: Dict[str, Component] = {}
    for item in components_section[1:]:
        if not (isinstance(item, list) and item and item[0] == "comp"):
            continue
        ref = ""
        comp = Component(ref="")
        for sub in item[1:]:
            kv = _kv(sub)
            if kv:
                k, v = kv
                if k == "ref":
                    ref = v
                    comp.ref = v
                elif k == "value":
                    comp.value = v
                elif k == "footprint":
                    comp.footprint = v
                elif k == "datasheet":
                    comp.datasheet = v
                elif k == "description":
                    comp.description = v
                continue
            if isinstance(sub, list) and sub:
                if sub[0] == "fields":
                    for fld in sub[1:]:
                        if isinstance(fld, list) and fld and fld[0] == "field":
                            name = ""
                            text = ""
                            for fsub in fld[1:]:
                                kv2 = _kv(fsub)
                                if kv2 and kv2[0] == "name":
                                    name = kv2[1]
                                elif isinstance(fsub, str):
                                    text = fsub
                            if name:
                                comp.fields[name] = text
                elif sub[0] == "property":
                    name = ""
                    val = ""
                    for psub in sub[1:]:
                        kv2 = _kv(psub)
                        if kv2:
                            if kv2[0] == "name":
                                name = kv2[1]
                            elif kv2[0] == "value":
                                val = kv2[1]
                    if name:
                        comp.properties[name] = val
                        if name == "Sheetname":
                            comp.sheetname = val
                        if name == "Sheetfile":
                            comp.sheetfile = val
                elif sub[0] == "libsource":
                    for lsub in sub[1:]:
                        kv2 = _kv(lsub)
                        if kv2:
                            if kv2[0] == "lib":
                                comp.lib = kv2[1]
                            elif kv2[0] == "part":
                                comp.part = kv2[1]
        if ref:
            comps[ref] = comp
    return comps


def parse_nets(nets_section: Any) -> List[Dict[str, Any]]:
    nets: List[Dict[str, Any]] = []
    for item in nets_section[1:]:
        if not (isinstance(item, list) and item and item[0] == "net"):
            continue
        net_name = ""
        net_code = ""
        net_class = ""
        nodes: List[Dict[str, str]] = []
        for sub in item[1:]:
            kv = _kv(sub)
            if kv:
                k, v = kv
                if k == "name":
                    net_name = v
                elif k == "code":
                    net_code = v
                elif k == "class":
                    net_class = v
                continue
            if isinstance(sub, list) and sub and sub[0] == "node":
                node: Dict[str, str] = {}
                for nsub in sub[1:]:
                    kv2 = _kv(nsub)
                    if kv2:
                        node[kv2[0]] = kv2[1]
                if "ref" in node and "pin" in node:
                    nodes.append(node)
        nets.append({"name": net_name, "code": net_code, "class": net_class, "nodes": nodes})
    return nets


POWER_NET_RE = re.compile(r"^(\\+\\d|\\+\\d\\.\\d|\\+3\\.3V|\\+5V|VBAT|VCC|VDD|VDDA|AVDD|DVDD|IOVDD|VSS|GND|AGND|PGND|VUSB|VBUS|VREG|VREF)", re.IGNORECASE)


def is_ic(ref: str) -> bool:
    return ref.startswith("U") and ref[1:].isdigit()


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract per-sheet connectivity summaries from KiCad .net")
    ap.add_argument("--netlist", default="OpenFC.net", help="Path to KiCad netlist (s-expression)")
    ap.add_argument("--outdir", default="analysis/netlist_extract", help="Output directory")
    args = ap.parse_args()

    netlist_path = Path(args.netlist)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    text = netlist_path.read_text(encoding="utf-8", errors="replace")
    tokens = tokenize_sexpr(text)
    root = parse_sexpr(tokens)
    sections = _find_sections(root)

    components_section = sections.get("components")
    nets_section = sections.get("nets")
    if components_section is None or nets_section is None:
        raise ParseError("missing components or nets section")

    comps = parse_components(components_section)
    nets = parse_nets(nets_section)

    # Build ref->pin->net mapping and capture pinfunction when present.
    for net in nets:
        net_name = net["name"]
        for node in net["nodes"]:
            ref = node.get("ref", "")
            pin = node.get("pin", "")
            if not ref or not pin or ref not in comps:
                continue
            comps[ref].connections[pin] = net_name
            if "pinfunction" in node:
                comps[ref].pinfunctions[pin] = node["pinfunction"]

    # Outputs
    # 1) Full component table (CSV)
    with (outdir / "components.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ref", "value", "footprint", "sheetname", "sheetfile", "lib", "part", "LCSC"])
        for ref in sorted(comps.keys(), key=lambda r: (re.sub(r"\\D", "", r) or "0", r)):
            c = comps[ref]
            w.writerow(
                [
                    c.ref,
                    c.value,
                    c.footprint,
                    c.sheetname,
                    c.sheetfile,
                    c.lib,
                    c.part,
                    c.properties.get("LCSC", c.fields.get("LCSC", "")),
                ]
            )

    # 2) IC list (JSON) with only "essential" info + connections
    ics: List[Dict[str, Any]] = []
    for ref, c in comps.items():
        if not is_ic(ref):
            continue
        ics.append(
            {
                "ref": c.ref,
                "value": c.value,
                "footprint": c.footprint,
                "sheetname": c.sheetname,
                "sheetfile": c.sheetfile,
                "lib": f"{c.lib}:{c.part}" if c.lib or c.part else "",
                "lcsc": c.properties.get("LCSC", c.fields.get("LCSC", "")),
                "datasheet_field": c.fields.get("Datasheet", c.datasheet),
                "connections": c.connections,
                "pinfunctions": c.pinfunctions,
            }
        )
    ics.sort(key=lambda x: x["ref"])
    (outdir / "ics.json").write_text(json.dumps(ics, indent=2, sort_keys=True), encoding="utf-8")

    # 3) Per-sheet IC lists
    per_sheet: Dict[str, List[Dict[str, Any]]] = {}
    for ic in ics:
        sheet = ic.get("sheetname") or ic.get("sheetfile") or "UNKNOWN"
        per_sheet.setdefault(sheet, []).append(ic)
    (outdir / "ics_by_sheet.json").write_text(json.dumps(per_sheet, indent=2, sort_keys=True), encoding="utf-8")

    # 4) Nets of interest (JSON)
    net_index: Dict[str, Dict[str, Any]] = {n["name"]: n for n in nets}
    power_nets = sorted([name for name in net_index.keys() if POWER_NET_RE.match(name)])
    (outdir / "power_nets.json").write_text(json.dumps(power_nets, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


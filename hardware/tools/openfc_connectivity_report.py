#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.openfc_pcb_extract import parse_board  # type: ignore


def sheet_from_net(net: str) -> str:
    if net.startswith("/"):
        parts = [p for p in net.split("/") if p]
        if parts:
            return parts[0]
    return "GLOBAL"


def norm(s: str) -> str:
    return s.replace("\n", " ").strip()


def compile_patterns(patterns: List[str]) -> List[re.Pattern[str]]:
    out: List[re.Pattern[str]] = []
    for p in patterns:
        out.append(re.compile(p))
    return out


def matches_any(net: str, pats: List[re.Pattern[str]]) -> bool:
    return any(p.search(net) for p in pats)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate human-readable net connectivity from OpenFC.kicad_pcb")
    ap.add_argument("--pcb", default="OpenFC.kicad_pcb", help="Path to KiCad PCB file")
    ap.add_argument("--outdir", default="analysis/net_connectivity", help="Output directory")
    ap.add_argument(
        "--expand",
        action="append",
        default=[],
        help="Regex for nets to fully expand in Markdown (repeatable). If omitted, uses defaults.",
    )
    ap.add_argument("--max-nodes", type=int, default=30, help="Max nodes to print for a net before truncating")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    default_expand = [
        r"^/ELRS/",
        r"^/UART",
        r"^/I2C_",
        r"^/IMU/",
        r"^/BLACKBOX/",
        r"^/OSD/",
        r"^/RP2350A/",
        r"^/PADS/",
        r"^Net-\(U36-USB_D[PM]\)",
        r"^/RP2350A/D[+-]$",
        r"^\+3\.3V",
        r"^\+5V",
        r"^\+BATT$",
        r"^VBUS|^VUSB",
        r"^GND$",
    ]
    expand_pats = compile_patterns(args.expand if args.expand else default_expand)

    footprints, _nets_by_id = parse_board(Path(args.pcb))

    net_nodes: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for fp in footprints:
        for pad in fp.pads:
            net = pad.net_name
            if not net:
                continue
            net_nodes[net].append(
                {
                    "ref": fp.ref,
                    "value": norm(fp.value),
                    "fp_id": norm(fp.fp_id),
                    "pad": norm(pad.number),
                    "pinfunction": norm(pad.pinfunction),
                }
            )

    # Write a full CSV for grepping/sorting externally.
    with (outdir / "nets.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sheet", "net", "ref", "value", "pad", "pinfunction", "fp_id"])
        for net in sorted(net_nodes.keys()):
            sheet = sheet_from_net(net)
            nodes = sorted(net_nodes[net], key=lambda n: (n["ref"], n["pad"]))
            for n in nodes:
                w.writerow([sheet, net, n["ref"], n["value"], n["pad"], n["pinfunction"], n["fp_id"]])

    # Markdown grouped by sheet, with truncation for very large nets.
    by_sheet: Dict[str, List[str]] = defaultdict(list)
    for net in sorted(net_nodes.keys()):
        by_sheet[sheet_from_net(net)].append(net)

    lines: List[str] = []
    lines.append("# OpenFC Net Connectivity (from PCB)")
    lines.append("")
    lines.append(f"Source: `{args.pcb}`")
    lines.append(f"Generated: `{outdir}/nets.md` and `{outdir}/nets.csv`")
    lines.append("")

    for sheet in sorted(by_sheet.keys()):
        lines.append(f"## {sheet}")
        lines.append("")
        for net in by_sheet[sheet]:
            nodes = sorted(net_nodes[net], key=lambda n: (n["ref"], n["pad"]))
            count = len(nodes)
            expand = matches_any(net, expand_pats)
            if (count > args.max_nodes) and not expand:
                # Keep a terse summary for large nets unless explicitly expanded.
                lines.append(f"- `{net}`: {count} nodes (truncated; add `--expand '{re.escape(net)}'` to force)")
                continue

            lines.append(f"### `{net}` ({count} nodes)")
            lines.append("")
            shown = nodes if count <= args.max_nodes else nodes[: args.max_nodes]
            for n in shown:
                pinfn = f" {n['pinfunction']}" if n["pinfunction"] else ""
                pad = f" pad {n['pad']}" if n["pad"] else ""
                lines.append(f"- `{n['ref']}`{pad}{pinfn} — {n['value']}")
            if count > len(shown):
                lines.append(f"- … {count - len(shown)} more nodes not shown")
            lines.append("")

    (outdir / "nets.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


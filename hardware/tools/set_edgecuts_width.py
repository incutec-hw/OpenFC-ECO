#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


GR_START_RE = re.compile(r"^\s*\(gr_\w+\b")
LAYER_EDGE_CUTS = '(layer "Edge.Cuts")'
WIDTH_LINE_RE = re.compile(r"^(\s*\(width\s+)([-+]?[0-9]*\.?[0-9]+)(\s*\)\s*)$")
STROKE_START_RE = re.compile(r"\(\s*stroke\b")


def _format_width(width_mm: float) -> str:
	# Match KiCad's typical compact formatting in saved files.
	return f"{width_mm:g}"


def update_gr_block(lines: list[str], width_mm: float) -> tuple[list[str], int]:
	if not any(LAYER_EDGE_CUTS in line for line in lines):
		return lines, 0

	out: list[str] = []
	changes = 0

	local_depth = 0
	in_stroke = False
	stroke_start_depth: int | None = None
	width_str = _format_width(width_mm)

	for line in lines:
		if not in_stroke and STROKE_START_RE.search(line):
			in_stroke = True
			stroke_start_depth = local_depth

		if in_stroke:
			match = WIDTH_LINE_RE.match(line)
			if match:
				new_line = f"{match.group(1)}{width_str}{match.group(3)}"
				if new_line != line:
					line = new_line
					changes += 1

		out.append(line)

		local_depth += line.count("(") - line.count(")")

		if in_stroke and stroke_start_depth is not None and local_depth <= stroke_start_depth:
			in_stroke = False
			stroke_start_depth = None

	return out, changes


def update_file(contents: list[str], width_mm: float) -> tuple[list[str], int]:
	out: list[str] = []
	changes = 0

	global_depth = 0
	in_block = False
	block_start_depth: int | None = None
	block_lines: list[str] = []

	def flush_block() -> None:
		nonlocal changes, block_lines
		updated, block_changes = update_gr_block(block_lines, width_mm)
		out.extend(updated)
		changes += block_changes
		block_lines = []

	for line in contents:
		if not in_block and GR_START_RE.match(line):
			in_block = True
			block_start_depth = global_depth
			block_lines = [line]
		elif in_block:
			block_lines.append(line)
		else:
			out.append(line)

		global_depth += line.count("(") - line.count(")")

		if in_block and block_start_depth is not None and global_depth == block_start_depth:
			in_block = False
			block_start_depth = None
			flush_block()

	if in_block:
		raise ValueError("Unclosed gr_* block while parsing; file may be malformed.")

	return out, changes


def main(argv: list[str]) -> int:
	parser = argparse.ArgumentParser(
		description='Set stroke width for gr_* objects on the "Edge.Cuts" layer in a KiCad .kicad_pcb file.',
	)
	parser.add_argument("pcb", type=Path, help="Path to .kicad_pcb file")
	parser.add_argument("--width-mm", type=float, default=0.05, help="Target stroke width in mm (default: 0.05)")
	parser.add_argument(
		"--write",
		action="store_true",
		help="Write changes back to the PCB file (default is dry-run)",
	)
	parser.add_argument(
		"--no-backup",
		action="store_true",
		help="Do not create a .bak copy when using --write",
	)
	args = parser.parse_args(argv)

	if args.width_mm <= 0:
		print("--width-mm must be > 0", file=sys.stderr)
		return 2

	pcb_path: Path = args.pcb
	if pcb_path.suffix != ".kicad_pcb":
		print(f"warning: {pcb_path} does not end with .kicad_pcb", file=sys.stderr)

	contents = pcb_path.read_text(encoding="utf-8").splitlines(keepends=True)
	updated, changes = update_file(contents, args.width_mm)

	if changes == 0:
		print("No Edge.Cuts stroke widths needed updating.")
		return 0

	if not args.write:
		print(f"Would update {changes} stroke width line(s). Re-run with --write to apply.")
		return 0

	if not args.no_backup:
		backup_path = pcb_path.with_suffix(pcb_path.suffix + ".bak")
		if backup_path.exists():
			print(f"Backup already exists: {backup_path}", file=sys.stderr)
			return 2
		shutil.copy2(pcb_path, backup_path)

	pcb_path.write_text("".join(updated), encoding="utf-8")
	print(f"Updated {changes} stroke width line(s) in {pcb_path}.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))


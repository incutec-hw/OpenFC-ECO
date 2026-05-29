# OpenFC-Lite-Mini — Project Instructions

## About this repo
OpenFC-Lite-Mini is an open-source Betaflight flight controller: **20×20 mm**, 6-layer, 3S–6S, built around the RP2354B. This repository covers the **Mini only**. The larger **30.5×30.5 mm OpenFC-Lite** will be a separate project derived from this one once the Mini is finalized; the two share the same schematic.

Design intent — a compact, low-cost FC:
- No barometer.
- No integrated ELRS receiver (use an external RX over UART).
- No onboard WS2812B LEDs (LED-strip pad only).
- Blackbox logging on a microSD slot (TF-021B-H265), not onboard SPI flash.

## Working agreement
- Stan is a hardware/embedded engineer. Be direct and critical — flag problems, skip praise.
- **Claude never edits schematics or board layouts.** Do not modify `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro` — not even a value/field swap. Claude produces analysis and **change lists**; Stan makes every schematic/PCB edit in KiCad himself. Pending schematic changes live in the README **Rev 2 Change List**.
- Never hand-edit a KiCad S-expression file. Read and analyze only — via kicad-skip, the pcbnew API, or kicad-cli.
- Claude may edit documentation (README, this file, other Markdown, JSON config/export files). Keep docs accurate — no aspirational content.
- Git: `main` is protected. Work on feature branches and open PRs via `gh`. Commit/push only when asked.
- Single source of truth is this file + README.md. No separate memory store.

## What Claude can / cannot do here
**Can:** review schematics, PCB, gerbers, netlists, footprints; trace nets; extract and manage the BOM; run DRC/ERC/DFM/EMC checks; power-budget and regulator analysis; SPICE simulation; component sourcing and pricing; fabrication-prep specs; documentation and diagrams; change lists and design specs.

**Cannot / will not:** edit schematic/PCB/project files; change nets or connections; add, remove, place, or route parts; place fab orders or take other irreversible external actions without explicit confirmation.

## Tools
- **Skills:** `kicad` (schematic/PCB analysis), `bom` (BOM lifecycle), `lcsc` / `digikey` / `mouser` / `element14` (sourcing + datasheets), `jlcpcb` / `pcbway` (fab prep), `emc` (pre-compliance), `spice` (simulation), `kidoc` (engineering docs).
- **Repo scripts** (`hardware/tools/`, read-only analysis): `audit_design.py`, `openfc_netlist_extract.py`, `openfc_connectivity_report.py`, `openfc_pcb_extract.py`, and helpers.
- **Environment (macOS):** kicad-skip lives in system Python 3.13 (`~/Library/Python/3.13/lib/python/site-packages`). `pcbnew` is only importable under KiCad's bundled Python (`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`). `kicad-cli` is at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
- **Headless net extraction (no pcbnew):** `kicad-cli sch export netlist --format kicadsexpr -o /tmp/x.net hardware/OpenFC.kicad_sch`, then `python3 hardware/tools/openfc_netlist_extract.py --netlist /tmp/x.net`.

## Revisions
- **Rev 1** — current physical prototype; received and in bench bring-up.
- **Rev 2** — next revision, in design. Change list in the README.

(No "V0.x" numbering — the earlier V0.1–V0.3 labels were export artifacts and are retired.)

## Key ICs (Rev 1 reference designators)
| Function | Ref | Part | LCSC | Bus / notes |
|---|---|---|---|---|
| MCU | U2 | RP2354B (QFN-80, 2 MB flash) | C39843328 | — |
| IMU | U9 | LSM6DSV16XTR (dev part) | C5267406 | SPI0; Rev 2 part undecided — see IMU |
| 10V buck (switchable) | U3 | LMR51430YFDDCR (3A) | C5219261 | EN=GPIO11; 4.7µH / 22µF 16V / FB 100k:6.49k → 9.85V |
| 5V buck (always-on) | U4 | LMR51430YFDDCR (3A) | C5219261 | 4.7µH inductor |
| 5V power mux | U5 | TPS2116DRLR | C3235557 | USB/BATT auto-select (clarify vs TPS2117 in Rev 2) |
| 3.3V LDO | U7 | LP5912-3.3DRVR | C524780 | 500 mA |
| 1.8V gyro LDO | U6 | NCV8187AMT180TAG | C893189 | 300 mA (Rev 2: ≥500 mA) |
| OSD comparator | U20 | TLV3201AIDBVR | C105188 | sync separator |
| OSD op-amp | U19 | TLV9061IDPWR | C2057878 | output buffer |
| OSD SPDT switch | U18 | SN74LVC1G3157DTBR | C2673087 | OSD pixel switch |
| microSD slot | Card1 | TF-021B-H265 | C498185 | SPI1 |
| VTX connector | U8 | SM06B-SRSS-TB (6-pin JST SH) | C160405 | digital VTX |
| ESC connector | P1 | 8-pin TH JST SH | — | pinout reversed — see Rev 2 |

## IMU
- The footprint is LGA-14 (2.5×3 mm) with pins 2/3 → GND and pins 10/11 → NC, which is electrically safe for **both TDK (ICM-426xx/456xx) and ST (LSM6D*) families**. Selecting/swapping the IMU is a field change once a part is chosen.
- Rev 1 populates **LSM6DSV16XTR** for development only.
- **The Rev 2 IMU is undecided** — to be chosen after more bench/flight testing.
- Family note: TDK parts use a CLKIN line to remove sample-timing jitter; ST parts have no CLKIN/SYNC. This interacts with the SPI-bus cleanup in the Rev 2 change list.

## GPIO map (RP2354B → Betaflight)
- UART0: TX=GPIO0, RX=GPIO1 (digital VTX on U8 JST SH connector)
- UART1: TX=GPIO22, RX=GPIO21 (external RX)
- PIO UART0: TX=GPIO2, RX=GPIO3
- PIO UART1: TX=GPIO26, RX=GPIO27
- Motors: M1=GPIO31, M2=GPIO30, M3=GPIO29, M4=GPIO28 (PIO0 DShot). **CRIT-2: order reversed vs the BF RP2350B reference config — resolve in firmware or swap silk (Rev 2).**
- SPI0 (IMU): SCK=GPIO18, MOSI=GPIO19, MISO=GPIO20, CS=GPIO14, INT=GPIO13
- IMU CLKIN: GPIO15 — wired but unused on an ST gyro; **Rev 2: drop CLKIN and group CS into the SPI bus** (revisit if a TDK IMU is chosen)
- SPI1 (microSD): SCK=GPIO42, MOSI=GPIO43, MISO=GPIO44, CS=GPIO46
- I2C0: SDA=GPIO16, SCL=GPIO17 (pull-ups to 3.3V; pin pairing SDA%4==0 / SCL%4==1 — keep if pins move)
- OSD (3 consecutive pins): OSD_W=GPIO33, OSD_EN=GPIO34, OSD_SYNC=GPIO35
- ADC (each via 1k+100nF RC): VBAT=GPIO41, CURRENT=GPIO40, RSSI=GPIO45, EXT=GPIO47
- LED strip: GPIO23 (PIO2). Status LED (LED0): GPIO12 — green on Rev 1, **must be blue (Rev 2)**.
- 10V enable: GPIO11. Beeper: GPIO6. SBUS invert: GPIO9 (**Rev 2: inverter removed**).
- Freed: GPIO24 (was ESP_EN), GPIO25 (was ESP_BOOT) — available for PINIO/telem.

## Power tree
```
+BATT → U3 (EN=GPIO11)           → +10V (switchable VTX/cam)   [inductor L2, out cap C28, FB R29 100k / R30]
+BATT → U4 (always-on)           → +5V_BUCK                    [inductor L3]
+5V_BUCK + +5V_USB → U5 (TPS2116 mux) → +5V → U7 (LP5912) → +3.3V → RP2354B VREG → +1.1V core
+5V → U6 (NCV8187)               → +1.8V_GYRO (IMU analog)
```

## PIO allocation
PIO0: DShot (motors). PIO1: PIO UARTs. PIO2: LED strip + OSD.

## Schematic structure
Hierarchical KiCad 9: root `OpenFC.kicad_sch` + 6 sub-sheets — `rp2350a`, `power`, `imu`, `osd`, `blackbox`, `pads`. (`baro`, `compass`, `elrs`, `leds` `.kicad_sch` are unreferenced leftovers slated for removal.)

## Connectors (JST SH, yellow preferred)
- **U8** — 6-pin SMD VTX: +10V / GND / TX / RX / GND / SBUS — matches the BF digital VTX standard ✓
- **P1** — 8-pin TH ESC: pinout reversed vs the BF 8-pin standard and missing a telemetry pin — **safety-critical, fix in Rev 2** (see change list).

## Layout rules
RP2350B buck and decoupling placement: see `hardware/tools/rp2350_layout_notes.md` (Raspberry Pi RP2350 datasheet §6.3.8.1 — buck C_IN/L/C_OUT must stay on the MCU side, copper cutaway under the switch node, etc.).

## Betaflight
- Target: Betaflight RP2350B (PICO platform); `BOARD_NAME = OPENFC_LITE_MINI_RP2350B`, `MANUFACTURER_ID = OPFC`. RP2354B uses the Pico SDK (C/C++) with PlatformIO.
- External RX over UART (no onboard/SPI RX).
- Analog OSD (FB_OSD) for RP2350B is still an open upstream PR stack (#14882 chain) — no flyable upstream binary yet; track before tape-out.
- Submission: schematic + config in `betaflight/config`; ~$500 T2 cloud-target fee. BF contacts: sugar K (project lead), vitroid (schematic-review channel).

## Repo conventions
- KiCad 9. Libraries are **project-local only**: `hardware/lib.kicad_sym`, `hardware/lib.pretty/`, `hardware/lib.3dshapes/`. Never global libraries.
- Python tools live in `hardware/tools/`.
- Production exports in `hardware/production/`, generated with the KiCad Fabrication Toolkit and named by revision (`rev1`, `rev2`, …). JLCPCB assembly; prefer LCSC basic parts.
- License: hardware under CERN-OHL-S.

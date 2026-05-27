# OpenFC-Lite-Mini

Open-source Betaflight flight controller — **20×20 mm**, 6-layer, 3S–6S, built around the RP2354B microcontroller. Compact and low-cost: external RX over UART, microSD blackbox, analog OSD.

<p>
<img src="images/openfc-lite-mini-rev1-top.png" width="400" alt="OpenFC-Lite-Mini Rev 1 Top" />
<img src="images/openfc-lite-mini-rev1-bottom.png" width="400" alt="OpenFC-Lite-Mini Rev 1 Bottom" />
</p>

> This repository is the **Mini** (20×20). A larger **OpenFC-Lite** (30.5×30.5 mm, bigger pads, more I/O, full-size SD) will be derived from this design once the Mini is finalized.

## At a glance

| | |
|---|---|
| MCU | RP2354B — dual Cortex-M33 @ 150 MHz, 2 MB flash, QFN-80 |
| IMU | 6-axis, SPI0 (LGA-14 footprint — part TBD, see [IMU](#imu)) |
| Blackbox | microSD card slot (TF-021B-H265) on SPI1 |
| OSD | analog, PIO-driven (sync separator + op-amp + SPDT switch) |
| Power | 3S–6S; switchable 10V (VTX/cam) + always-on 5V |
| Size | 20×20 mm, 6-layer |
| RX | external, over UART |
| USB | USB-C, USB-CDC for configuration |

Intentionally omitted to keep it small and cheap: barometer, integrated ELRS receiver, onboard WS2812B LEDs (LED-strip pad only), onboard SPI blackbox flash (microSD instead).

## Status

Rev 1 boards have been received and brought up. The custom Betaflight target builds and flashes; USB enumeration, IMU, SD card blackbox, and the switchable 10V VTX rail are confirmed working on bench. Bring-up of motors, external RX, and the analog OSD chain is in progress. See the [Rev 2 Change List](#rev-2-change-list) for hardware fixes scheduled for the next revision.

## Specifications

### Core
- **MCU:** RP2354B — dual-core ARM Cortex-M33 @ 150 MHz, 2 MB integrated stacked flash, QFN-80
- **IMU:** 6-axis MEMS on SPI0, dedicated 1.8V analog LDO (see [IMU](#imu))
- **Blackbox:** TF-021B-H265 microSD card slot on SPI1
- **USB:** USB-C, USB-CDC for configuration

### Power tree
| Rail | Source | Regulator | Notes |
|---|---|---|---|
| +10V (switchable) | +BATT | LMR51420YFDDCR (U3, 2A) | EN gated by GPIO11 (PINIO1). VTX/cam rail. 3A drop-in: LMR51430YFDDCR. |
| +5V (always-on) | +BATT | LMR51420YFDDCR (U4, 2A) | 3A drop-in: LMR51430YFDDCR. |
| +5V (USB/BATT mux) | +5V_BUCK + +5V_USB | TPS2116DRLR (U5) | Auto-selects active source. |
| +3.3V | +5V | LP5912-3.3DRVR (U7) | 500 mA LDO. |
| +1.8V (gyro analog) | +5V | NCV8187AMT180TAG (U6) | Isolated supply for IMU noise rejection. |
| +1.1V (MCU core) | +3.3V | RP2354B internal VREG | — |

### Motor outputs
- 4× PIO-driven DShot outputs (DShot600, bidirectional telemetry supported)
- M1=GPIO31, M2=GPIO30, M3=GPIO29, M4=GPIO28

### Connectors
- **USB-C** — configuration and firmware flashing
- **U8** — 6-pin SMD JST SH digital VTX connector (matches Betaflight standard: +10V/GND/TX/RX/GND/SBUS)
- **P1** — 8-pin TH JST SH ESC harness *(reversed pinout on Rev 1 — must mirror + add telem in Rev 2)*
- **J7/J8** — I2C0 expansion pads (SDA/SCL, with pull-ups to 3.3V)

### Serial / I/O
- **UART0** (GPIO0/1) — digital VTX / MSP DisplayPort
- **UART1** (GPIO22/21) — external serial RX (CRSF/SBUS/etc.)
- **PIO UART0** (GPIO2/3) — software UART, default GPS
- **PIO UART1** (GPIO26/27) — software UART, spare
- **I2C0** (GPIO16/17) — external expansion
- **SPI0** (GPIO18/19/20, CS=GPIO14, INT=GPIO13) — IMU
- **SPI1** (GPIO42/43/44, CS=GPIO46) — microSD blackbox

### Analog inputs
- VBAT sense (GPIO41) — 100k/10k divider, 11:1 ratio, 1k+100nF RC filter
- Current sense (GPIO40) — onboard sense circuit, 1k+100nF RC filter
- RSSI (GPIO45) — 1k+100nF RC filter
- External ADC (GPIO47) — 1k+100nF RC filter

### Additional
- Addressable LED strip output (GPIO23, PIO2)
- Status LED (GPIO12)
- Beeper output (GPIO6)
- 10V rail enable (GPIO11) — exposed as PINIO1/USER1 in firmware

### Analog OSD
- TLV3201AIDBVR (U20) — fast comparator, sync separator on incoming composite video
- TLV9061IDPWR (U19) — op-amp output buffer to the camera signal
- SN74LVC1G3157DTBR (U18) — SPDT analog switch: camera passthrough, black-pixel inject, white-pixel inject
- Driven by RP2354B PIO2 — pixel-level timing for character overlay on PAL/NTSC composite

## IMU

The IMU footprint is LGA-14 (2.5×3 mm), routed with pins 2/3 → GND and pins 10/11 → NC, so it accepts **both TDK (ICM-426xx/456xx) and ST (LSM6D*) families**. Choosing the IMU is a part-population decision, not a layout change.

- **Rev 1** populates **LSM6DSV16XTR** for development only.
- **The Rev 2 IMU is not yet decided** — to be selected after more bench and flight testing.
- Note: TDK parts use a CLKIN line to eliminate sample-timing jitter; ST parts have no CLKIN/SYNC. This couples to the SPI-bus cleanup in the change list below.

## Firmware

A custom Betaflight target (`OPENFC_LITE_MINI_RP2350B`, `MANUFACTURER_ID = OPFC`, `FC_TARGET_MCU = RP2350B`) defines:

- Motor map matching the Rev 1 silkscreen (M1..M4 = GPIO31..GPIO28)
- `USE_SDCARD_SPI` on SPI1 for blackbox
- `USE_PINIO` on GPIO11 for the switchable 10V VTX rail
- FB_OSD framework wired but disabled by default (enable once the analog OSD chain is verified on hardware — note the RP2350B FB_OSD driver is still an open upstream PR stack)

Build (requires a Betaflight checkout with `pico-sdk` and the BF-pinned ARM toolchain):

```sh
make picotool_install
make arm_sdk_install
make CONFIG=OPENFC_LITE_MINI_RP2350B
```

Output is a `.uf2` in `obj/`. Hold BOOTSEL, plug in USB, and drag the UF2 onto the `RP2350` mass-storage drive that mounts.

## PIO Allocation

The RP2350B has 3 PIO blocks × 4 state machines (12 total):

| Block | Function |
|---|---|
| PIO0 | DShot motor output (4 SMs, one per motor) |
| PIO1 | Software UART (PIO UART0 + PIO UART1 — TX and RX programs) |
| PIO2 | LED strip + analog OSD pixel timing |

## Revision History

| Rev | Status | Notes |
|---|---|---|
| **Rev 1** | current | Received and in bench bring-up |
| **Rev 2** | in design | See [Rev 2 Change List](#rev-2-change-list) |

## Rev 2 Change List

Schematic changes for the next revision. **Schematic and board edits are done manually** — this list is the spec to run down.

Legend: 🔧 field swap (value/part only) · 🔌 wiring / topology change · 🔍 decision / investigation

### Power
- 🔧 **HW-1 — C28** (10V buck output cap): 16V → **25V**, 22µF 0603. DC-bias derating + transient headroom.
- 🔧 **HW-2 — R30** (10V FB, bottom of R29=100k divider): 6.8k → **6.34k** (E96). Corrects output 9.42V → 10.06V.
- 🔧 **HW-3 — L2** (10V inductor): 4.7µH → **10µH** (FTC303020D100MBCA, C7423323). ⚠️ The 10µH was mistakenly applied to **L3 (5V rail)**; **L2 (10V)** is the rail that actually needs it.
- 🔧 **L3** (5V inductor) field fix: Value says 10µH but MPN/LCSC still the old 4.7µH part. Make consistent — revert to 4.7µH unless 10µH is intended.
- 🔧 **HW-5 — U3/U4** bucks (optional): LMR51420 (2A) → **LMR51430** (3A), C5219261. Drop-in, same SOT-23-6.
- 🔧 **HW-8 — U6** gyro LDO: NCV8187 (300 mA) → **≥500 mA** in the same WDFN-6 footprint (part TBD; BF §3.1.2).

### MCU / USB (per Raspberry Pi RP2350 datasheet)
- 🔧 **R12 / R13** USB series resistors: 30Ω → **27Ω**.
- 🔧 **R14** VREG_AVDD resistor: 30Ω → **33Ω**.
- 🔍 **D1** USB ESD (USBLC6-2P6): keep or remove? ESD on USB alone — but not the other exposed pads — is inconsistent. Decide.

### LEDs
- 🔌 All status/indicator LEDs: **0201 → 0402** (0201 too fragile — broke during nut install). Footprint change.
- 🔧 **HW-4 — D2** (LED0 status, GPIO12): green → **blue** (BF §3.1.4.6 requires blue LED0). D4/D5/D7/D10 are power-rail indicators.
- 🔧 LED series resistors: raise (too bright); recompute per rail voltage. Production colors TBD (purple needs >3.3V).

### Signals / connectivity (wiring — manual)
- 🔌 **SPI0 cleanup**: group **GYRO_CS** into the SPI bus (with SCK/MOSI/MISO); drop the IMU **CLKIN/SYNC** net (GPIO15) — ST gyros have no SYNC. Same regroup for **FLASH_CS** (SD). ⚠️ If a TDK IMU is chosen, CLKIN is useful — couple to the IMU decision.
- 🔌 **Remove SBUS inverter** (GPIO9 / SBUS_INVERT circuit).
- 🔌 **HW-6 — ESC connector P1**: mirror reversed pinout **+ add telemetry pin** (BF 8-pin: Current = pin 3, Telem = pin 4). **Safety-critical** — current pinout shorts VBAT to a GPIO on a standard BF harness.
- 🔌 **HW-7** — Add **battery reverse-polarity protection** (PMOS RPP).
- 🔌 **HW-11 — Beeper**: active buzzer + NPN driver (300–1000Ω base R) per BF §3.1.4.
- 🔌 **SD card**: wire compatible with both SPI and SDIO; use SPI for now, switch to SDIO via a BF update if supported on Pico.

### Decisions / investigations
- 🔍 **IMU** — undecided for Rev 2; see [IMU](#imu).
- 🔍 **U5 power MUX** — clarify TPS2116 vs TPS2117 (which part/behavior is intended).
- 🔍 **SDIO on Pico** — does Betaflight support SDIO blackbox on RP2350B? (Madflight wants it too.)
- 🔍 **CRIT-2 — motor order** M1–M4 reversed vs the Betaflight RP2350B reference config — resolve in the firmware target or swap silk.
- 🔍 **CRIT-3 — FB_OSD upstream**: the RP2350B analog-OSD driver PR stack (#14882) is still open; no flyable upstream binary yet. Track before tape-out.
- 🔍 Add **SWD connector** (4-pin JST SH: 3V3/GND/SWDIO/SWCLK) per BF.

## Repository Structure

```
OpenFC-Lite-Mini/
├── README.md
├── LICENSE
├── hardware/                ← KiCad 9 project, libraries, and production files
│   ├── OpenFC.kicad_pro     ← Project file
│   ├── OpenFC.kicad_pcb     ← PCB layout
│   ├── OpenFC.kicad_sch     ← Top-level schematic (hierarchical)
│   ├── *.kicad_sch          ← Sub-sheets
│   ├── lib.kicad_sym        ← Project-local symbol library
│   ├── lib.pretty/          ← Project-local footprint library
│   ├── lib.3dshapes/        ← Project-local 3D models
│   ├── production/          ← JLCPCB production exports, per revision
│   └── tools/               ← Analysis scripts (Python, kicad-skip / pcbnew API)
└── images/                  ← Board renders
```

All symbol, footprint, and 3D model libraries are project-local — no external library setup required.

## Schematic Hierarchy

- `OpenFC.kicad_sch` — top-level
- `rp2350a.kicad_sch` — RP2354B microcontroller and supporting circuitry
- `power.kicad_sch` — power supply and regulation (10V buck, 5V buck, 3.3V/1.8V LDOs, 5V mux)
- `imu.kicad_sch` — 6-axis IMU on SPI0 (LGA-14 2.5×3 footprint; Rev 1 populates LSM6DSV16XTR for dev — see [IMU](#imu))
- `osd.kicad_sch` — analog OSD chain (TLV3201 sync sep + TLV9061 buffer + SN74LVC1G3157 switch)
- `blackbox.kicad_sch` — TF-021B-H265 microSD card slot
- `pads.kicad_sch` — solder pads and connectors

## License

Hardware licensed under [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt). See [LICENSE](LICENSE) for details.

# OpenFC-Lite — Project Instructions

## What This Is
Open-source Betaflight flight controller — **Lite (stripped) variant** of OpenFC (formerly "ECO"). 30x30mm, 6-layer, 3S-6S.
No baro, no integrated ELRS receiver, no WS2812B onboard LEDs. SD card slot replaces onboard blackbox flash. Same MCU, IMU, OSD, and power design as the full OpenFC.

## Key ICs
| IC | Part | LCSC | Bus |
|----|------|------|-----|
| MCU | RP2354B (QFN-80, 2MB flash) | C39843328 | — |
| IMU | ICM-42688-P | C2904815 | SPI0 (GPIO18-20), CS=GPIO14, INT=GPIO13 |
| 10V Buck (sw) | LMR51420YFDDCR (2A) | C7296200 | EN=GPIO11; pin-compat drop-in to 3A: LMR51430YFDDCR (C5219261) |
| 5V Buck (always-on) | LMR51420YFDDCR (2A) | C7296200 | pin-compat drop-in to 3A: LMR51430YFDDCR (C5219261) |
| 3.3V LDO | LP5912-3.3DRVR | C524780 | — |
| 1.8V Gyro LDO | NCV8187AMT180TAG | C893189 | — |
| 5V Power Mux | TPS2116DRLR | C3235557 | — |
| OSD sync-sep comparator | TLV3201AIDBVR | C105188 | — |
| OSD buffer op-amp | TLV9061IDPWR | C2057878 | — |
| OSD SPDT switch | SN74LVC1G3157DTBR | C2673087 | OSD_EN=GPIO34 |
| SD card slot | TF-021B-H265 | C498185 | SPI1 (GPIO42-44), CS=GPIO46 |

## Removed vs Full OpenFC
| Removed | Part | Reason |
|---------|------|--------|
| Barometer | BMP388 | Cost reduction — not needed for acro/racing |
| Blackbox Flash (onboard SPI) | BY25Q128ASWIG | Replaced with TF-021B-H265 microSD slot |
| ELRS Receiver | ESP32-C3FH4 + SX1281 + antenna + matching | Cost reduction — use external receiver via UART |
| WS2812B LEDs | XL-1010RGBC-WS2812B (x4 instances, 16 LEDs total) | Cost reduction |
| Compass | LIS3MDLTR | Was already DNP in full version |
| ELRS 3.3V LDO | WL9005D4-33 | Not needed without ELRS |

## GPIO Map (RP2354B → Betaflight)
- UART0: TX=GPIO0, RX=GPIO1 (digital VTX on U1 JST SH connector)
- UART1: TX=GPIO22, RX=GPIO21 (available for external RX)
- PIO UART0: TX=GPIO2, RX=GPIO3
- PIO UART1: TX=GPIO26, RX=GPIO27
- Motors: M1=GPIO31, M2=GPIO30, M3=GPIO29, M4=GPIO28 (PIO0 DShot). **NOTE CRIT-2: reversed vs BF OPENFC_RP2350B reference (M1=PA28..M4=PA31)**
- OSD (FB_OSD, 3 consecutive pins): OSD_W=GPIO33, OSD_EN=GPIO34, OSD_SYNC=GPIO35
- SBUS invert ctrl: GPIO9
- IMU INT2 (ODR sync): GPIO15
- I2C0: SDA=GPIO16, SCL=GPIO17 (exposed on J7/J8 pads, R41/R42 pull-ups to 3.3V)
- SPI0 (IMU): SCK=GPIO18, MOSI=GPIO19, MISO=GPIO20
- SPI1 (SD card): SCK=GPIO42, MOSI=GPIO43, MISO=GPIO44, CS=GPIO46
- ADC: VBAT=GPIO41, CURRENT=GPIO40, RSSI=GPIO45, EXT=GPIO47 (all with 1k+100nF RC filter)
- LED strip: GPIO23 (PIO2), Status LED: GPIO12
- 10V enable: GPIO11, Beeper: GPIO6
- Freed GPIOs: GPIO24 (was ESP_EN), GPIO25 (was ESP_BOOT) — available for PINIO or telem

## Power Tree
+BATT → LMR51420 (U6, EN via GPIO11) → +10V (switchable, VTX/cam rail)
+BATT → LMR51420 (U7, always-on) → +5V_BUCK
+5V_BUCK + +5V_USB → TPS2116 mux → +5V → LP5912 → +3.3V → RP2354B VREG → +1.1V (core)
+5V → NCV8187 → +1.8V_GYRO (IMU analog)

## PIO Allocation
PIO0: DShot (motors), PIO1: PIO UARTs, PIO2: LED strip + OSD

## V0.3 Known Issues (ordered, fix in V0.4)
- **C28 (22µF 0603 16V on +10V rail)**: 16V rating too low for 10V output — severe DC bias derating + no transient headroom. Change to 25V rated (e.g., CL10A226MQ8NRNC).
- **R30 (6.8k)**: gives 9.42V not 10V. Change to 6.34k (E96) for 10.06V output.
- **L2 (4.7µH)**: undersized for 10V rail at 6S input (116% ripple). Change to ~10µH (FTC303020D100MBCA, C7423323, same 3x3 footprint).
- **D7 (green)**: LED0 must be blue — **hard requirement** per BF manufacturer design guidelines §3.1.4.6. Green LED0 fails manufacturer certification. LED0 (blue, required), LED1 (green, preferred), LED2 (amber, optional). See https://betaflight.com/docs/development/manufacturer/manufacturer-design-guidelines#3146-leds and https://betaflight.com/docs/development/FC-LEDs.
- **U3/U4 (LMR51420YFDDCR 2A)**: drop-in upgrade to LMR51430YFDDCR (C5219261) for 3A headroom. Same footprint/pinout.

## Open Issues
1. **CRIT-2**: Motor pin numbering M1-M4 reversed vs BF OPENFC_RP2350B reference config — fix in board config.h OR swap J1-J4 labels.
2. **CRIT-3**: OSD FB_OSD 3-pin mapping remapped to GPIO4=W, GPIO5=EN, GPIO6=SYNC (consecutive, per BF PR#14882). **No upstream BF driver merged yet.**
3. **CRIT-4**: No battery reverse polarity protection.
4. ~~**CRIT-5**: ESC connector P1 reversed~~ — **FIXED in V0.3**, pinout now matches BF 8-pin standard.
5. **Blue LED0**: D7 is green; BF manufacturer design guidelines §3.1.4.6 **require** LED0 to be blue. Not cosmetic — green LED0 fails manufacturer certification. Must change for V0.4.

## Schematic Structure
`hardware/` — KiCad 9 hierarchical: root `OpenFC.kicad_sch` + sub-sheets:
rp2350a, power, pads, osd, imu, blackbox

`blackbox.kicad_sch` holds the TF-021B-H265 microSD slot (replaces onboard SPI flash). Sub-sheet was rebuilt via `hardware/tools/rebuild_blackbox.py` (kicad-sch-api). UUIDs match PCB.

## Connectors (JST SH, yellow preferred)
- **U1 (6-pin digital VTX, SMD)**: +10V, GND, DIGITAL_TX, DIGITAL_RX, GND, SBUS — **matches BF digital VTX standard ✓**
- **P1 (8-pin ESC, TH)**: currently reversed — see CRIT-5 above

## Rules
- **NEVER** raw-edit `.kicad_sch`, `.kicad_pcb`, `.kicad_pro` — use Python scripts with kicad-skip or pcbnew API
- Python tools live in `hardware/tools/`
- Libraries are project-local: `hardware/lib.kicad_sym`, `hardware/lib.pretty/`, `hardware/lib.3dshapes/`
- Production exports in `hardware/production/` — use KiCad Fabrication Toolkit for JLCPCB
- JLCPCB assembly, prefer LCSC basic parts

## Firmware
- Target: Betaflight RP2350B (PICO platform)
- No firmware in this repo yet
- RP2354B uses Pico SDK (C/C++), PlatformIO
- No ELRS firmware needed (external receiver)

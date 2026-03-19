# OpenFC-ECO — Project Instructions

## What This Is
Open-source Betaflight flight controller — **ECO (stripped) variant** of OpenFC. 30x30mm, 4-layer, 2S-6S.
No baro, no blackbox flash, no integrated ELRS receiver, no WS2812B onboard LEDs. Same MCU, IMU, OSD, and power design as the full OpenFC.

## Key ICs
| IC | Part | LCSC | Bus |
|----|------|------|-----|
| MCU | RP2354B (QFN-80, 2MB flash) | C39843328 | — |
| IMU | LSM6DSV16XTR | C5267406 | SPI0 (GPIO18-20), CS=GPIO14, INT=GPIO13 |
| 12V Buck | LMR51420YDDCR/YFDDCR | C5383002/C7296200 | — |
| 3.3V LDO | LP5912-3.3DRVR | C524780 | — |
| 1.8V Gyro LDO | NCV8187AMT180TAG | C893189 | — |
| Power Mux | TPS2116DRLR | C3235557 | — |
| OSD Mux | PI3A223ZMEX | — | GPIO32-37 |

## Removed vs Full OpenFC
| Removed | Part | Reason |
|---------|------|--------|
| Barometer | BMP388 | Cost reduction — not needed for acro/racing |
| Blackbox Flash | BY25Q128ASWIG | Cost reduction — use SD card logger or no logging |
| ELRS Receiver | ESP32-C3FH4 + SX1281 + antenna + matching | Cost reduction — use external receiver via UART |
| WS2812B LEDs | XL-1010RGBC-WS2812B (x4 instances, 16 LEDs total) | Cost reduction |
| Compass | LIS3MDLTR | Was already DNP in full version |
| ELRS 3.3V LDO | WL9005D4-33 | Not needed without ELRS |

## GPIO Map (RP2354B → Betaflight)
- UART0: TX=GPIO0, RX=GPIO1
- UART1: TX=GPIO22 (funcsel 11 UART_AUX), RX=GPIO21 (available for external RX)
- PIO UART0: TX=GPIO2, RX=GPIO3
- PIO UART1: TX=GPIO26, RX=GPIO27
- Motors: M1=GPIO31, M2=GPIO30, M3=GPIO29, M4=GPIO28 (PIO0 DShot)
- OSD: VBLACK=GPIO32, SYNC_IN=GPIO33, PIXEL_SEL=GPIO34, VWHITE=GPIO35, COLOR_SEL=GPIO36, SYNCLVL=GPIO37
- ADC: VBAT=GPIO41, CURRENT=GPIO40, RSSI=GPIO45, EXT=GPIO47
- LED strip: GPIO23 (PIO2), Status LED: GPIO12
- 10V enable: GPIO11, Beeper: GPIO6
- Freed GPIOs: GPIO24 (was ESP_EN), GPIO25 (was ESP_BOOT), GPIO46 (was BB_CS), SPI1 bus (GPIO42-44)

## Power Tree
+BATT → LMR51420 → +12V (switchable via GPIO11) / +5V_BUCK (always on)
+5V_BUCK + VBUS → TPS2116 mux → +5V → LP5912 → +3.3V → RP2354B VREG → +1.1V
+5V → NCV8187 → +1.8V_GYRO

## PIO Allocation
PIO0: DShot (motors), PIO1: PIO UARTs, PIO2: LED strip + OSD

## Open Issues (inherited from OpenFC, ELRS issues dropped)
1. **CRIT-2**: Motor pin numbering M1-M4 reversed vs BF config
2. **CRIT-3**: OSD needs 3 consecutive pins for FB_OSD (remap GPIO33=W, 34=EN, 35=SYNC)
3. **CRIT-4**: No battery reverse polarity protection

## Schematic Structure
`hardware/` — KiCad 9 hierarchical: root `OpenFC.kicad_sch` + sub-sheets:
rp2350a, power, pads, osd, imu

Sheets to remove from baseline (copied from full OpenFC): elrs, Radioschematic, leds, baro, blackbox, compass, connectors

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

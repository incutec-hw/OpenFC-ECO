# OpenFC-Lite EMC Checklist

## Noise sources (ranked by threat)

| Source | Frequency | Notes |
|---|---|---|
| LMR51420/30 bucks U3, U4 | 1.1 MHz fundamental + harmonics to ~200 MHz | Strongest radiator |
| RP2350 internal core buck | ~400 kHz variable | Hard to isolate, close to MCU |
| 12 MHz crystal X1 | 12 MHz + harmonics | Can alias into RX bands |
| DShot600 motor outputs | 600 kHz, 12-20 ns edges | Broadband from fast edges |
| SPI0 IMU clock | up to 10 MHz | Low level, well shielded |
| SPI1 SD card | up to 25 MHz | Bursty, noisy |
| USB D+/D- | 12 Mbps FS | Contained if routed right |

## 1. Buck switch node loops (L2, L3)

- CIN GND + COUT GND on local top-side island, NOT merged into main GND pour
- 2 adjacent stitching vias per buck to inner GND plane
- SW node: just wide enough for current (~0.5 mm), short (<5 mm), minimum area
- No GND pour directly under SW trace on top AND on layer 2
- No GND pour directly under inductor body
- L2 and L3 >5 mm apart (avoid mutual coupling)
- FB trace away from SW node, under a GND shield layer

## 2. IMU (U9 LSM6DSV16X) immunity

- Place >=10 mm from any switch node (L1, L2, L3)
- Over solid inner GND plane, no splits underneath
- 1.8V_GYRO rail: continuous GND return, no crossings
- NCV8187 LDO output within 5 mm of IMU VDD pin
- IMU CS/SCK/MOSI/MISO tightly grouped with GND ref, NOT over SW nodes
- 100 nF VDD + 100 nF VDDIO within 1 mm of pins
- SPI1 (SD card) not parallel to SPI0 (IMU) with <0.5 mm spacing

## 3. ADC inputs (VBAT, CURRENT, RSSI, EXT)

- RC filters (1k + 100nF) within 5 mm of MCU ADC pins (already in schematic)
- ADC traces short, routed over GND plane
- VBAT divider resistors away from buck switch nodes
- No long traces parallel to digital clocks

## 4. USB D+/D-

- 27 ohm series R immediately next to MCU pins 66/67
- 90 ohm differential impedance target
- Continuous GND plane beneath full length, no splits
- GND stitching vias flanking any layer transition
- USBLC6 ESD AT connector (not near MCU)
- CC1/CC2 5.1 kOhm pull-downs present and correct

## 5. Motor outputs M1-M4

- On board edge (already - P1)
- 22-33 ohm series R in-line at MCU (currently 0 ohm)
- Route over GND plane, distance from IMU
- DShot edges radiate

## 6. Crystal X1 (12 MHz)

- Crystal + 2 load caps directly under XIN/XOUT pins, <3 mm stubs
- GND guard ring tied to inner plane via 2+ vias
- No ground flood BETWEEN XIN/XOUT traces
- Load caps same side as crystal
- No high-speed signals within 5 mm

## 7. Power rail filtering / bulk caps

- Bulk 47-100 uF low-ESR electrolytic at BATT input (ceramics alone insufficient)
- +5V and +10V outputs: ferrite bead + bulk cap at each connector (VTX, RX)
- Common-mode choke or ferrite bead on VTX 10V line helps conducted EMI
- Large ground copper area around each regulator

## 8. Connector ESD / surge

- TVS 5V uni-directional on every external I/O pad:
  - RX UART, SBUS, LED strip, Buzzer, Current sense, RSSI, Cam video
- Currently only USB has ESD (USBLC6) - ADD protection to others
- Series R (100-470 ohm) on LED strip + ESD diode
- Series R on beeper drive

## 9. GND plane topology (6-layer)

- Solid continuous GND plane on layer 2 under top signals, no splits
- No separate analog/digital GND islands
- Star point: all power-entry GNDs meet at same pour region
- GND stitching vias every 5-10 mm
- No splits under IMU, ADC pins, or crystal

## 10. RX / VTX rail considerations

- No onboard RF on ECO (ELRS removed)
- LED_STRIP output kept away from UART lines (WS2812 bursts noisy)
- 10V VTX rail traces >=20 mil wide, inner plane or heavy top/bottom copper
- Bulk 22-47 uF electrolytic at VTX connector for load transients
- Optional: ferrite bead in series before bulk cap

## 11. Signal integrity

- DShot600 PIO outputs: if trace >30 mm, add 22-33 ohm series termination
- SPI1 (SD card) at 25 MHz: <50 mm bus, same layer, continuous GND ref
- LED_STRIP 1 MHz bursts: 22 ohm series at MCU output

## 12. Shielding / enclosure

- Mounting hole via stitches for frame-as-shield (optional)
- Conformal coating over buck area (usually not needed for FPV)

## Priority

**Must-fix before fab:**
1. Buck hot-loop GND islands + separate stitching vias (U3, U4)
2. SW node area minimization + copper cutaway beneath
3. IMU physical distance from L1/L2/L3 (>=10 mm)
4. USB ESD placed AT connector, GND continuity under diff pair
5. Crystal guard ring + direct placement under XIN/XOUT

**Strongly recommended:**
6. 22-33 ohm series on motor lines + LED strip
7. ESD diodes on RX UART, Current, RSSI, Video pads
8. Bulk electrolytic at battery input and VTX connector
9. Ferrite bead + bulk on 5V/10V outputs to connectors

**Nice to have:**
10. Common-mode choke on USB D+/D-
11. Conformal coating zone around bucks

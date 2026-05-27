# OpenFC-Lite Design Audit

Generated from `OpenFC.kicad_sch` + `OpenFC.kicad_pcb` via kicad-skip + pcbnew.

## 1. Top-level Hierarchy

| Sheetname | File | On disk |
|---|---|---|
| BLACKBOX | `blackbox.kicad_sch` | yes |
| IMU | `imu.kicad_sch` | yes |
| OSD | `osd.kicad_sch` | yes |
| RP2350A | `rp2350a.kicad_sch` | yes |
| PADS | `pads.kicad_sch` | yes |
| POWER | `power.kicad_sch` | yes |

Root schematic: `OpenFC.kicad_sch` — 6 sub-sheet(s) referenced.

## 2. Component Inventory

Total placed refs: **168** (DNP excluded: 1).

### MCU (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U36 | RP2354B_C39843328 | RP2354B | C39843328 | Raspberry Pi | QFN-80_L10.0-W10.0-P0.40-TL-EP3.4 | rp2350a |

### IMU (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U14 | LSM6DSV16XTR | LSM6DSV16XTR | C5267406 | STMicroelectronics | LGA-14_L3.0-W2.5-P0.50-BR | imu |

### Buck (2)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U6 | LMR51420YFDDCR | LMR51420YFDDCR | C7296200 | Texas Instruments | SOT-23-6_L2.9-W1.6-P0.95-LS2.9-BL | power |
| U7 | LMR51420YFDDCR | LMR51420YFDDCR | C7296200 | Texas Instruments | SOT-23-6_L2.9-W1.6-P0.95-LS2.9-BL | power |

### LDO (2)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U13 | LP5912-3.3DRVR | LP5912-3.3DRVR | C524780 | Texas Instruments | WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm | power |
| U21 | NCV8187AMT180TAG | NCV8187AMT180TAG | C893189 | onsemi | WDFN-6_L2.0-W2.0-P0.65-BL-EP | power |

### Power Mux (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U33 | TPS2116DRLR | TPS2116DRLR | C3235557 | Texas Instruments | SOT-583-8_L2.1-W1.6-P0.50-LS1.6-BL | power |

### OSD (3)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U34 | TLV3201AIDBVR | TLV3201AIDBVR | C105188 | Texas Instruments | SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR | osd |
| U35 | SN74LVC1G3157DTBR | SN74LVC1G3157DTBR | C2673087 | Texas Instruments | X2SON-6_L1.0-W0.8-BL | osd |
| U38 | TLV9061IDPWR | TLV9061IDPWR | C2057878 | Texas Instruments | X2SON-4_L0.8-W0.8-P0.48-TL-DPW | osd |

### SD card (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| Card2 | TF-021B-H265 | TF-021B-H265 | C498185 | - | TF-SMD_TF-021B-H265 | blackbox |

### USB (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| USB1 | TYPE-C 16P QTWT | TYPE-C 16P QTWT | C5187472 | SHOU HAN | USB-TYPE-C-SMD_TYPE-C-16P-QTWT | rp2350a |

### Switch (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U32 | TS2306A 240GF MSM 9_C2976675 | TS2306A 240gf MSM 9 | C2976675 | SHOU HAN | SW-SMD_4P-L3.0-W2.0-P0.85-LS3.5 | rp2350a |

### MOSFET (4)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| Q1 | DMN1150UFB-7B | DMN1150UFB-7B | C459538 | Diodes Incorporated | DFN-3L_L1.0-W0.6-P0.65-BR | power |
| Q2 | DMN1150UFB-7B | DMN1150UFB-7B | C459538 | Diodes Incorporated | DFN-3L_L1.0-W0.6-P0.65-BR | rp2350a |
| Q3 | DMN1150UFB-7B | DMN1150UFB-7B | C459538 | Diodes Incorporated | DFN-3L_L1.0-W0.6-P0.65-BR | rp2350a |
| Q7 | DMN1150UFB-7B | DMN1150UFB-7B | C459538 | Diodes Incorporated | DFN-3L_L1.0-W0.6-P0.65-BR | rp2350a |

### Diode/LED (5)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| D1 | LED_1_Green | XL-0201UGC | C3646922 | XINGLIGHT | LED_0201_0603Metric | power |
| D2 | LED_1_Green | XL-0201UGC | C3646922 | XINGLIGHT | LED_0201_0603Metric | rp2350a |
| D4 | LED_1_Green | XL-0201UGC | C3646922 | XINGLIGHT | LED_0201_0603Metric | power |
| D5 | LED_1_Green | XL-0201UGC | C3646922 | XINGLIGHT | LED_0201_0603Metric | power |
| D7 | LED_1_Green | XL-0201UGC | C3646922 | XINGLIGHT | LED_0201_0603Metric | power |

### Diode (4)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| D3 | RB161QS-40_C28646385 | RB161QS-40 | C28646385 | ROHM | SOD-882_L1.0-W0.6-RD | power |
| D8 | USBLC6-2P6 | USBLC6-2P6 | C15999 | STMicroelectronics | SOT-666 | rp2350a |
| D9 | SDM02U30LP3-7B | SDM02U30LP3-7B | C151629 | Diodes Incorporated | X3-DFN0603-2_L0.6-W0.3-RD | osd |
| D21 | RB161QS-40_C28646385 | RB161QS-40 | C28646385 | ROHM | SOD-882_L1.0-W0.6-RD | power |

### IC (1)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| U1 | SM06B-SRSS-TB(LF)(SN) | SM06B-SRSS-TB(LF)(SN) | C160405 | JST | CONN-SMD_SM06B-SRSS-TB-LF-SN | pads |

### Inductor (3)

| Ref | Value | MPN | LCSC | Mfr | Footprint | Sheet |
|---|---|---|---|---|---|---|
| L1 | AOTA-B201610S3R3-101-T | AOTA-B201610S3R3-101-T | C42411119 | Abracon | IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T | rp2350a |
| L3 | XRTC303020D4R7MBCA | XRTC303020D4R7MBCA | C39846837 | XR | IND-SMD_L3.0-W3.0_AFE303020S | power |
| L4 | XRTC303020D4R7MBCA | XRTC303020D4R7MBCA | C39846837 | XR | IND-SMD_L3.0-W3.0_AFE303020S | power |

### Connector / Solder Pads (54)

(full net list in section 14)

| Footprint | Sheet | Count |
|---|---|---|
| small_pad | pads | 54 |

### Passives summary

| Function | Placed | DNP |
|---|---|---|
| Resistor | 44 | 0 |
| Capacitor | 38 | 0 |
| Test Pad | 0 | 0 |

## 3. Power Tree

```
+BATT -> U6 (LMR51420YFDDCR buck) -> +12V   [switchable via GPIO11 via Q?]
+BATT -> U7 (LMR51420YFDDCR buck) -> +5V_BUCK
+5V_BUCK -+
          +- U33 (TPS2116 mux) -> +5V
VBUS(USB)-+
+5V -> U13 (LP5912-3.3) -> +3.3V
+3.3V -> U36 (RP2354B VREG) -> +1.1V_CORE (DVDD)
+5V -> U21 (NCV8187 LDO) -> +1.8V_GYRO
```

| Ref | Role | MPN | Footprint | Pad → Net |
|---|---|---|---|---|
| U6 | 12V buck | LMR51420YFDDCR | SOT-23-6_L2.9-W1.6-P0.95-LS2.9-BL | 1→GND; 2→Net-(U6-SW); 3→+BATT; 4→Net-(U6-FB); 5→/POWER/10V_ENABLE; 6→Net-(U6-CB) |
| U7 | 5V buck | LMR51420YFDDCR | SOT-23-6_L2.9-W1.6-P0.95-LS2.9-BL | 1→GND; 2→Net-(U7-SW); 3→+BATT; 4→Net-(U7-FB); 5→+BATT; 6→Net-(U7-CB) |
| U13 | 3.3V LDO | LP5912-3.3DRVR | WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm | 1→+3.3V; 2→unconnected-(U13-NC-Pad2); 3→GND; 4→+5V; 5→GND; 6→+5V; 7→GND; → |
| U21 | 1.8V gyro LDO | NCV8187AMT180TAG | WDFN-6_L2.0-W2.0-P0.65-BL-EP | 1→+5V; 2→+5V; 3→GND; 4→/POWER/1.8V_PG; 5→+1.8V_GYRO; 6→+1.8V_GYRO |
| U33 | 5V power mux | TPS2116DRLR | SOT-583-8_L2.1-W1.6-P0.50-LS1.6-BL | 1→GND; 2→+5V; 3→+5V_BUCK; 4→Net-(U33-PR1); 5→+5V_BUCK; 6→+5V_USB; 7→+5V; 8→unconnected-(U33-ST-Pad8) |

## 4. Bypass caps per power rail

| Rail | Net | # Caps to GND | Cap refs |
|---|---|---|---|
| +BATT | +BATT | 2 | C35, C37 |
| +12V | — (net not found) | - | - |
| +5V_BUCK | +5V_BUCK | 1 | C40 |
| +5V | +5V | 3 | C32, C33, C48 |
| VBUS | — (net not found) | - | - |
| +3.3V | +3.3V | 17 | C1, Card2, C3, C16, C30, C31, C34, C42, C43, C44, C49, C50, C51, C52, C65, C67, C69 |
| +1.8V_GYRO | +1.8V_GYRO | 2 | C2, C41 |
| +1.1V | +1.1V | 4 | C27, C28, C29, C68 |
| +1.1V_CORE | — (net not found) | - | - |
| DVDD | — (net not found) | - | - |

Rail-like nets present:

`+10V`, `+5V`, `+5V_BUCK`, `+5V_USB`, `/POWER/10V_ENABLE`

## 5. ADC Inputs

| Role | Net | MCU pad | Resistors on net | Bypass caps to GND |
|---|---|---|---|---|
| VBAT_SENSE | /RP2350A/ADC_VBAT | 52 | R35, R43 | C56 |
| CURR_SENSE | /PADS/CURRENT | 49 | — | **NONE** |
| RSSI | /PADS/RSSI | 56 | — | **NONE** |
| EXT | — not found | - | - | - |

**Check**: A CURRENT-sense ADC input WITHOUT a bypass cap at the MCU pin is a Betaflight MFG-guideline violation (noise couples straight into ADC).

## 6. SPI Buses & CS pull-ups

| Signal | Net | Refs on net | Resistors (pull-ups?) |
|---|---|---|---|
| SPI0 SCK | — | - | - |
| SPI0 MOSI | — | - | - |
| SPI0 MISO | — | - | - |
| IMU CS | /IMU/GYRO_CS | U14, U36 | — |
| SD CS | /BLACKBOX/BB_CS | Card2, R2, U36 | R2 |
| SD MOSI | — | - | - |
| SD MISO | — | - | - |
| SD SCK | — | - | - |

### CS pull-up check (to +3.3V)

| CS line | Net | Pull-up present? | Pull-up ref |
|---|---|---|---|
| IMU_CS (U14 pad 12) | /IMU/GYRO_CS | NO | - |
| SD_CS (Card2 pad 2) | /BLACKBOX/BB_CS | YES | R2 |

## 7. Status LEDs (non-WS2812)

| Ref | Value/Color | MPN | Pad nets | Likely MCU-side net |
|---|---|---|---|---|
| D1 | LED_1_Green | XL-0201UGC | →, 1→GND, 2→Net-(D1-A) | , Net-(D1-A) |
| D2 | LED_1_Green | XL-0201UGC | →, 1→GND, 2→Net-(D2-A) | , Net-(D2-A) |
| D4 | LED_1_Green | XL-0201UGC | →, 1→GND, 2→Net-(D4-A) | , Net-(D4-A) |
| D5 | LED_1_Green | XL-0201UGC | →, 1→GND, 2→Net-(D5-A) | , Net-(D5-A) |
| D7 | LED_1_Green | XL-0201UGC | →, 1→Net-(D7-K), 2→Net-(D7-A) | , Net-(D7-K), Net-(D7-A) |

Blue LED (Betaflight LED0 requirement): **MISSING** (none)

## 8. I2C Pull-ups

| Signal | Net | Refs on net | Pull-up to 3.3V |
|---|---|---|---|
| I2C_SDA | /I2C_SDA | J7, R42, U36 | YES |
| I2C_SCL | /I2C_SCL | J8, R41, U36 | YES |

## 9. RP2354B (U36) Pinout

| Pad | Net |
|---|---|
| 3 | /RP2350A/BEEPER |
| 5 | +3.3V |
| 7 | /RP2350A/SBUS_INVERT |
| 9 | /POWER/10V_ENABLE |
| 10 | +1.1V |
| 11 | /RP2350A/LED0 |
| 12 | /IMU/GYRO_INT |
| 13 | /IMU/GYRO_CS |
| 14 | /IMU/SPI0.CLKIN |
| 15 | +3.3V |
| 16 | /I2C_SDA |
| 17 | /I2C_SCL |
| 18 | /IMU/SPI0.SCK |
| 19 | /IMU/SPI0.MOSI |
| 20 | /IMU/SPI0.MISO |
| 21 | /UART1_RX |
| 22 | /UART1_TX |
| 23 | /RP2350A/LED_STRIP_L |
| 24 | +3.3V |
| 25 | /RP2350A/ESP_EN |
| 26 | /RP2350A/ESP_BOOT |
| 27 | /PADS/PIOUART1_TX |
| 28 | /PADS/PIOUART1_RX |
| 29 | +3.3V |
| 30 | /RP2350A/XIN |
| 31 | /RP2350A/XOUT |
| 32 | +1.1V |
| 35 | Net-(U36-RUN) |
| 36 | /PADS/M4 |
| 37 | /PADS/M3 |
| 38 | /PADS/M2 |
| 39 | /PADS/M1 |
| 41 | +3.3V |
| 42 | /OSD/OSD_W |
| 43 | /OSD/OSD_EN |
| 44 | /OSD/OSD_SYNC |
| 49 | /PADS/CURRENT |
| 50 | +3.3V |
| 51 | +1.1V |
| 52 | /RP2350A/ADC_VBAT |
| 53 | /BLACKBOX/SPI1.SCK |
| 54 | /BLACKBOX/SPI1.MOSI |
| 55 | /BLACKBOX/SPI1.MISO |
| 56 | /PADS/RSSI |
| 57 | /BLACKBOX/BB_CS |
| 58 | /PADS/ADC2 |
| 59 | Net-(U36-ADC_AVDD) |
| 60 | +3.3V |
| 61 | Net-(U36-VREG_AVDD) |
| 62 | GND |
| 63 | Net-(U36-VREG_LX) |
| 64 | +3.3V |
| 65 | +1.1V |
| 66 | Net-(U36-USB_DM) |
| 67 | Net-(U36-USB_DP) |
| 68 | +3.3V |
| 69 | +3.3V |
| 75 | Net-(U36-QSPI_SS) |
| 76 | +3.3V |
| 77 | /PADS/DIGITAL_TX |
| 78 | /PADS/DIGITAL_RX |
| 79 | /PADS/PIOUART0_TX |
| 80 | /PADS/PIOUART0_RX |
| 81 | GND |

## 10. OSD Circuit

| Ref | Value | Footprint | Pad → Net |
|---|---|---|---|
| U34 | TLV3201AIDBVR | SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR | 1→/OSD/OSD_SYNC; 2→GND; 3→/OSD/VID_DC; 4→GND; 5→+3.3V |
| U38 | TLV9061IDPWR | X2SON-4_L0.8-W0.8-P0.48-TL-DPW | 1→Net-(U38-OUT); 2→Net-(U38-IN-); 3→GND; 4→Net-(U35-A); 5→+3.3V |
| U35 | SN74LVC1G3157DTBR | X2SON-6_L1.0-W0.8-BL | 1→/OSD/OSD_LVL; 2→GND; 3→/OSD/VIDEO_IN; 4→Net-(U35-A); 5→+3.3V; 6→/OSD/OSD_EN |

## 11. SD Card (Blackbox)

| Ref | Value | Footprint | Pad → Net |
|---|---|---|---|
| Card2 | TF-021B-H265 | TF-SMD_TF-021B-H265 | 1→Net-(Card2-DAT2); 2→/BLACKBOX/BB_CS; 3→/BLACKBOX/SPI1.MOSI; 4→+3.3V; 5→/BLACKBOX/SPI1.SCK; 6→GND; 7→/BLACKBOX/SPI1.MISO; 8→Net-(Card2-DAT1); 9→GND; 10→GND |

## 12. Motor Outputs (M1-M4)

| Motor net | Refs on net |
|---|---|
| /PADS/M1 | J4, P1, U36 |
| /PADS/M2 | J3, P1, U36 |
| /PADS/M3 | J2, P1, U36 |
| /PADS/M4 | J1, P1, U36 |

## 13. Reset / Boot

- **RUN**: net `Net-(U36-RUN)` — refs: R36, U36
- U36 pad 35 (RUN) connects to `Net-(U36-RUN)`; refs on net: R36, U36

## 14. Connectors & Pads

### Solder Pads / Connectors

| Ref | Footprint | Pad → Net |
|---|---|---|
| J1 | small_pad | /PADS/M4 |
| J2 | small_pad | /PADS/M3 |
| J3 | small_pad | /PADS/M2 |
| J4 | small_pad | /PADS/M1 |
| J5 | small_pad | GND |
| J6 | small_pad | +5V |
| J7 | small_pad | /I2C_SDA |
| J8 | small_pad | /I2C_SCL |
| J9 | small_pad | GND |
| J13 | small_pad | +5V |
| J14 | small_pad | GND |
| J15 | small_pad | /LED |
| J16 | small_pad | +5V |
| J17 | small_pad | GND |
| J18 | small_pad | /LED |
| J19 | small_pad | +5V |
| J20 | small_pad | GND |
| J21 | small_pad | /LED |
| J22 | small_pad | +5V |
| J23 | small_pad | GND |
| J24 | small_pad | /PADS/CURRENT |
| J25 | small_pad | GND |
| J27 | small_pad | +BATT |
| J28 | small_pad | +10V |
| J29 | small_pad | GND |
| J30 | small_pad | /LED |
| J32 | small_pad | /OSD/VIDEO_IN |
| J33 | small_pad | /OSD/VIDEO_OUT |
| J34 | small_pad | +5V |
| J35 | small_pad | /PADS/DIGITAL_TX |
| J36 | small_pad | /PADS/DIGITAL_RX |
| J37 | - |  |
| J38 | small_pad | /PADS/SBUS |
| J39 | small_pad | +5V |
| J40 | small_pad | /PADS/BUZZER- |
| J41 | small_pad | GND |
| J42 | small_pad | GND |
| J43 | small_pad | /UART1_TX |
| J44 | small_pad | /UART1_RX |
| J45 | small_pad | /PADS/PIOUART0_RX |
| J46 | small_pad | /PADS/PIOUART0_TX |
| J47 | small_pad | GND |
| J48 | small_pad | +5V |
| J49 | small_pad | +5V |
| J50 | small_pad | GND |
| J51 | small_pad | GND |
| J52 | small_pad | /PADS/ADC2 |
| J53 | small_pad | +5V |
| J54 | small_pad | GND |
| J55 | small_pad | /PADS/PIOUART1_TX |
| J56 | small_pad | /PADS/RSSI |
| J57 | small_pad | /PADS/PIOUART1_RX |
| J58 | small_pad | +10V |
| J59 | small_pad | +3.3V |

### USB

| Ref | Footprint | Pad → Net |
|---|---|---|
| USB1 | USB-TYPE-C-SMD_TYPE-C-16P-QTWT | p0→GND; p→; pA1→GND; pA4→+5V_USB; pA5→Net-(USB1-CC1); pA6→/RP2350A/D+_C; pA7→/RP2350A/D-_C; pA9→+5V_USB; pA12→GND; pB5→Net-(USB1-CC2); pB6→/RP2350A/D+_C; pB7→/RP2350A/D-_C |

## 15. CLAUDE.md GPIO map cross-check

| GPIO | CLAUDE.md function | U36 pad | Net |
|---|---|---|---|
| GPIO0 | UART0 TX | 77 | /PADS/DIGITAL_TX |
| GPIO1 | UART0 RX | 78 | /PADS/DIGITAL_RX |
| GPIO2 | PIO UART0 TX | 79 | /PADS/PIOUART0_TX |
| GPIO3 | PIO UART0 RX | 80 | /PADS/PIOUART0_RX |
| GPIO6 | Beeper | 3 | /RP2350A/BEEPER |
| GPIO11 | 10V enable | 9 | /POWER/10V_ENABLE |
| GPIO12 | Status LED | 11 | /RP2350A/LED0 |
| GPIO13 | IMU INT | 12 | /IMU/GYRO_INT |
| GPIO14 | IMU CS | 13 | /IMU/GYRO_CS |
| GPIO18 | IMU SCK | 18 | /IMU/SPI0.SCK |
| GPIO19 | IMU MISO | 19 | /IMU/SPI0.MOSI |
| GPIO20 | IMU MOSI | 20 | /IMU/SPI0.MISO |
| GPIO21 | UART1 RX | 21 | /UART1_RX |
| GPIO22 | UART1 TX | 22 | /UART1_TX |
| GPIO23 | LED strip | 23 | /RP2350A/LED_STRIP_L |
| GPIO26 | PIO UART1 TX | 27 | /PADS/PIOUART1_TX |
| GPIO27 | PIO UART1 RX | 28 | /PADS/PIOUART1_RX |
| GPIO28 | M4 | 36 | /PADS/M4 |
| GPIO29 | M3 | 37 | /PADS/M3 |
| GPIO30 | M2 | 38 | /PADS/M2 |
| GPIO31 | M1 | 39 | /PADS/M1 |
| GPIO32 | OSD VBLACK | — | — (GPIO not wired on MCU) |
| GPIO33 | OSD SYNC_IN | 42 | /OSD/OSD_W |
| GPIO34 | OSD PIXEL_SEL | 43 | /OSD/OSD_EN |
| GPIO35 | OSD VWHITE | 44 | /OSD/OSD_SYNC |
| GPIO36 | OSD COLOR_SEL | — | — (GPIO not wired on MCU) |
| GPIO37 | OSD SYNCLVL | — | — (GPIO not wired on MCU) |
| GPIO40 | CURRENT ADC | 49 | /PADS/CURRENT |
| GPIO41 | VBAT ADC | 52 | /RP2350A/ADC_VBAT |
| GPIO45 | RSSI ADC | 56 | /PADS/RSSI |
| GPIO47 | EXT ADC | 58 | /PADS/ADC2 |

GPIOs wired on MCU but not documented in CLAUDE.md:

| GPIO | U36 pad | Net |
|---|---|---|
| GPIO9 | 7 | /RP2350A/SBUS_INVERT |
| GPIO15 | 14 | /IMU/SPI0.CLKIN |
| GPIO16 | 16 | /I2C_SDA |
| GPIO17 | 17 | /I2C_SCL |
| GPIO24 | 25 | /RP2350A/ESP_EN |
| GPIO25 | 26 | /RP2350A/ESP_BOOT |
| GPIO42 | 53 | /BLACKBOX/SPI1.SCK |
| GPIO43 | 54 | /BLACKBOX/SPI1.MOSI |
| GPIO44 | 55 | /BLACKBOX/SPI1.MISO |
| GPIO46 | 57 | /BLACKBOX/BB_CS |

## 16. Audit findings

| Severity | Finding |
|---|---|
| HIGH | CURRENT-sense net `/PADS/CURRENT` has NO bypass cap to GND — add ~100nF near MCU ADC pin. |
| LOW | RSSI ADC net `/PADS/RSSI` has no bypass cap to GND (acceptable for PWM/analog RSSI). |
| HIGH | IMU CS net `/IMU/GYRO_CS` (U14 pad 12) has NO pull-up to 3.3V — floating CS at boot can cause bus contention; add 10k to +3.3V. |
| MED | No explicit BLUE LED found for Betaflight LED0 status. |


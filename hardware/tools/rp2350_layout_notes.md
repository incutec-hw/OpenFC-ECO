# RP2350B Two-Sided Layout Rules

Source: RP2350 Datasheet §6.3.8.1, Hardware Design with RP2350 guide (Raspberry Pi).

## Hard constraint — buck regulator must stay on MCU side

Direct quote from RP2350 Datasheet §6.3.8.1:

> "Don't place any of C_IN / L_X / C_OUT on the opposite side of the PCB."
> "Follow this layout as closely as possibly."

This means the following MUST stay on the top side with the MCU:

| Ref | Part | Role |
|---|---|---|
| C_IN (4.7µF) | Buck input cap | part of high-current hot loop |
| L_X (L1, 3.3µH, Abracon AOTA-B201610S3R3-101-T, 0806) | Buck inductor | switch-node path |
| C_OUT (4.7µF) | Buck output cap | part of hot loop |
| R3 (33Ω) + C9 (4.7µF) | VREG_AVDD filter | needs own GND via back to QFN pad |
| DVDD 100nF × 2 (nearest regulator) | Core decoupling | part of COUT hot loop |

Footprint zone: ~6×4 mm cluster near pins 60-65.

Additional rules for this zone:
- Cut away copper immediately under L_X / VREG_LX switch node trace on top layer AND inner layer 2 (6-layer boards)
- GND vias back to QFN center pad: use **2 adjacent vias** to reduce impedance, "short-as-possible"
- CFILT GND path MUST NOT share vias with C_IN/C_OUT high-current GND
- VREG_FB: feed from COUT output, do NOT route under LX

## Can go on bottom side

| Component | Rule |
|---|---|
| DVDD 100nF × 4-5 (far from regulator, opposite edge of QFN) | 2 GND vias per cap |
| 2nd 4.7µF on V_OUT (C10, opposite edge) | Explicitly recommended by RPi to be AWAY from regulator |
| IOVDD 100nF caps (all 8) | 2 GND vias per cap, directly under pin |
| QSPI_IOVDD 100nF (pin 69) | same |
| USB_OTP_VDD 100nF (pin 5) | same |
| ADC_AVDD 100nF (pin 60 area) | same |
| Crystal (12 MHz) + load caps | Risky but doable — see crystal notes |
| USB ESD diode + Type-C connector | OK after R7/R8 |

## Crystal on bottom — caveats

- RP2350 uses 10.5 pF total load, ~3 pF parasitic budget
- Each via adds 0.3-0.5 pF → 2 vias = ~1 pF budget consumed
- Place crystal directly under XIN/XOUT pins (pins 30/31), minimize stubs
- Both load caps on same side as crystal
- May need to retune R2 (1kΩ damping) or load caps (try 12pF instead of 15pF)
- No ground flood between XIN/XOUT; maintain GND reference plane

## USB — near-MCU placement

- R7/R8 (27Ω series termination): stay on **top side** immediately adjacent to pins 66/67
- Differential pair can transition to bottom via vias AFTER the series resistors
- Add flanking GND vias at layer transition for return-path continuity
- Solid uninterrupted GND beneath D+/D- the entire length

## Summary strategy for OpenFC-Lite

Top side (MCU-only vision not achievable — keeps these):
- RP2354B MCU
- Buck cluster: C_IN, L1, C_OUT, R3, C9 (~5 small parts, ~6×4 mm)
- 2 DVDD 100nF caps closest to regulator
- USB R7/R8 27Ω series resistors

Bottom side:
- 4-5 remaining DVDD 100nF caps + 4.7µF C10 on opposite QFN edge
- All IOVDD / QSPI_IOVDD / USB_OTP_VDD / ADC_AVDD 100nF caps
- Crystal + load caps (directly under pins 30/31)
- USB ESD diode + USB-C connector
- All other support circuits (LDOs, power mux, IMU, OSD, SD card, connectors etc.)

## Sources

- RP2350 Datasheet: https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- Hardware Design with RP2350: https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
- Reference RP2350B FC designs: madflight FC3v2, TichyTech rp2350-flight-controller

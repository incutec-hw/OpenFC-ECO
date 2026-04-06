# OpenFC-ECO

Stripped-down variant of [OpenFC](https://github.com/Just4Stan/OpenFC) — open-source Betaflight flight controller based on the RP2354B microcontroller. Same core design, fewer peripherals, lower cost.

<p>
<img src="images/openfc-eco-v03-top.png" width="400" alt="OpenFC-ECO V0.3 Top" />
<img src="images/openfc-eco-v03-bottom.png" width="400" alt="OpenFC-ECO V0.3 Bottom" />
</p>

## What's Different from OpenFC

| Feature | OpenFC | OpenFC-ECO |
|---------|--------|------------|
| MCU | RP2354B | RP2354B |
| IMU | LSM6DSV16XTR | LSM6DSV16XTR |
| Barometer | BMP388 | **Removed** |
| Blackbox | BY25Q128ASWIG (16MB SPI flash) | **MicroSD card slot** |
| ELRS Receiver | ESP32-C3FH4 + SX1281 (break-off) | **Removed** |
| Onboard WS2812B LEDs | 16x (4 corners) | **Removed** |
| OSD | PIO-based analog | PIO-based analog |
| Power | 3S-6S, 10V/5V | 3S-6S, 10V/5V |

## Features

### Microcontroller
- **RP2354B** - Raspberry Pi dual-core ARM Cortex-M33 @ 150MHz (with integrated flash)

### Sensors
- **IMU**: LSM6DSV16XTR

### Motor Outputs
- 4x PWM/DShot motor outputs

### Analog OSD on PIO
Hardware implementation of opamp and mux to detect syncs and select between white and black pixels.

### Connectivity
- **USB-C** - Configuration and firmware flashing
- **UART0** - Serial RX/TX
- **UART1** - Serial port (for external receiver)
- **PIO UART** - Software UART via RP2350 PIO (2x)
- **I2C** - External sensor expansion
- **SPI** - IMU bus

### Analog Inputs
- Current sensor input (ADC)
- RSSI input (ADC)
- 1 external available ADC input

### Additional Features
- Addressable LED strip output (WS2812/NeoPixel)
- Buzzer output
- Status LED

### Power
- 3S-6S batteries
- 10V and 5V regulated outputs, 10V is switchable

## Repository Structure

```
OpenFC-ECO/
├── README.md
├── hardware/          ← KiCad project, libraries, and production files
│   ├── OpenFC.kicad_pro
│   ├── *.kicad_sch    ← Hierarchical schematics
│   ├── OpenFC.kicad_pcb
│   ├── lib.kicad_sym  ← Custom symbol library
│   ├── lib.pretty/    ← Custom footprint library
│   ├── lib.3dshapes/  ← 3D models
│   └── tools/         ← Analysis scripts
└── images/            ← Board renders
```

All symbol, footprint, and 3D model libraries are included in the repository — no external library setup required.

## Schematic Hierarchy

- `OpenFC.kicad_sch` - Top-level schematic
- `rp2350a.kicad_sch` - RP2354B microcontroller and supporting circuitry
- `power.kicad_sch` - Power supply and regulation
- `imu.kicad_sch` - LSM6DSV16XTR IMU
- `osd.kicad_sch` - OSD circuitry
- `blackbox.kicad_sch` - MicroSD card slot (blackbox logging)
- `pads.kicad_sch` - Solder pads and connectors

## License

Licensed under [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt). See [LICENSE](LICENSE) for details.

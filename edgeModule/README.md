# Edge Module

Firmware template for BlueMesh relay nodes with dual board targets.

## Targets

- `esp32dev` (legacy path): NimBLE + ESP32 Wi-Fi AP/STA
- `portenta_c33` (default): ArduinoBLE + C33 Wi-Fi client mode

## Build

```bash
# Default (Portenta C33)
pio run

# Explicit target
pio run -e portenta_c33

# Flash
pio run -e portenta_c33 -t upload
pio device monitor
```

## BLE GATT contract

- Service UUID: `7f8f0100-1b22-4f6c-a133-8f0f9a2e1001`
- Config characteristic (read/write): `7f8f0101-1b22-4f6c-a133-8f0f9a2e1001`
- Status characteristic (read): `7f8f0102-1b22-4f6c-a133-8f0f9a2e1001`

Write payload format:

```text
moduleId=node-001;upstreamSsid=CenterBackhaul;upstreamPass=secret;token=abc123;apSsid=BlueMesh-node-001;apPass=changeme123
```

## Portenta C33 note

The current Portenta path provisions over BLE and joins upstream Wi-Fi.
ESP32-specific softAP client-count telemetry is not available on C33 in this scaffold.

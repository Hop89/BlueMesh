# Edge Module

ESP32 starter firmware for BlueMesh relay nodes.

## Goals

- Receive provisioning data over BLE
- Host local Wi-Fi AP for nearby users
- Join upstream Wi-Fi for backhaul to center node
- Emit heartbeat metrics to center service (next step)

## Build

```bash
pio run
pio device monitor
```

This scaffold intentionally leaves secure BLE provisioning and heartbeat transport as TODO items.

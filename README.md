# BlueMesh

Starter scaffold for low-cost community connectivity extension.

## Project layout

- `centerModule/` Node.js center service with module registry API and dashboard
- `centerModule/tools/ble_provision.py` Python `bleak` provisioning client
- `edgeModule/` ESP32 firmware template for BLE provisioning + Wi-Fi AP/backhaul
- `shared/protocol.md` enrollment and heartbeat contract draft

## First run

### Center service

```bash
cd centerModule
cp .env.example .env
npm install
npm run dev
```

### BLE provisioner

```bash
cd centerModule
python -m pip install -r tools/requirements.txt
python tools/ble_provision.py --module-id node-001 --upstream-ssid CenterBackhaul --upstream-pass changeme123 --center-url http://localhost:8080
```

### Edge module

```bash
cd edgeModule
pio run
pio device monitor
```

## Important design note

Bluetooth is used for provisioning/control only. User traffic rides Wi-Fi AP plus Wi-Fi backhaul for usable throughput.

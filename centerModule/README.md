# Center Module

This folder hosts the central control service that:
- Exposes a module registry API
- Accepts module heartbeats
- Serves a simple dashboard for operations

## Quick start

```bash
npm install
npm run dev
```

Service defaults to `http://0.0.0.0:8080`.

## API

- `GET /health`
- `GET /api/modules`
- `POST /api/modules`
- `POST /api/modules/:moduleId/heartbeat`
- `POST /api/provision/token`

## BLE provisioning client (Python + bleak)

`tools/ble_provision.py` provisions an edge module over BLE by writing GATT config data.

### Install

```bash
cd centerModule
python -m pip install -r tools/requirements.txt
```

### Run

```bash
python tools/ble_provision.py --module-id node-001 --upstream-ssid CenterBackhaul --upstream-pass changeme123 --center-url http://localhost:8080
```

If auto-discovery fails, pass `--address <BLE_MAC_OR_ADDRESS>`.

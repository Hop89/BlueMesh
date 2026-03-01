# BlueMesh

BlueMesh currently has two active workflows:

1. Bluetooth computer-to-computer chat GUI (`centerModule/src/BTChatGUI.py`)
2. BLE provisioning flow for edge modules (`centerModule/tools/ble_provision.py` + `edgeModule/` firmware)

## Project Layout

- `centerModule/` Node.js center API (provision token + module routes)
- `centerModule/src/BTChatGUI.py` Bluetooth chat GUI (chat, host-routed weather/search/email)
- `centerModule/src/emailHandler.py` email send/check helpers used by chat GUI
- `centerModule/tools/ble_provision.py` BLE provisioning client (`bleak`)
- `edgeModule/` firmware targets (`portenta_c33`, `esp32dev`)
- `shared/protocol.md` draft protocol notes

## Requirements

- Python 3.10+
- Node.js 18+
- PlatformIO CLI (for firmware build/flash)
- Two Bluetooth-capable computers for chat testing

Install Python deps used by provisioning/chat:

```bash
python -m pip install -r centerModule/tools/requirements.txt
python -m pip install mailtrap python-dotenv
```

## Bluetooth Chat Client (Host + Client)

The GUI script:

- Host (`Server` mode) listens for Bluetooth RFCOMM connection
- Client (`Client` mode) connects to host Bluetooth MAC
- Host can send files to client
- Weather/search/email requests from client are executed on host and returned over Bluetooth

Run on both machines:

```bash
cd centerModule
python src/BTChatGUI.py
```

### Host Setup

1. Set mode to `Server`
2. Keep host bind as `00:00:00:00:00:00` (or adapter MAC if needed)
3. Pick port (default `4`)
4. Click `Connect/Start`

### Client Setup

1. Pair both computers in OS Bluetooth settings first
2. Set mode to `Client`
3. Enter host Bluetooth MAC in `Server MAC`
4. Use same port as host
5. Click `Connect/Start`

### Chat Feature Notes

- `Send File` button is host-only; received files are saved to:
  `~/Downloads/BlueMeshInbox`
- `Get Weather API` returns a 5-day forecast
- `Search Web API` uses DuckDuckGo instant answer API
- `Send Email` and `Check Email` in client mode forward requests to host

## Email Setup For Chat GUI

Email config is loaded from:

- `centerModule/src/.env`

Add at least:

```env
MAILTRAP_TOKEN=your_mailtrap_token
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
MAIL_SENDER=hello@demomailtrap.co
MAIL_SENDER_NAME=BlueMesh
```

Without these values, email send/check will fail and log an error in the GUI.

## Center API (Needed For Provisioning)

```bash
cd centerModule
npm install
npm run dev
```

Default API host/port are from `centerModule/.env` (or defaults in code).

## Provision Edge Module Over BLE

1. Build and flash firmware (`edgeModule/`) to your board (for example Portenta C33)
2. Run center API (`npm run dev`)
3. Run provisioning tool:

```bash
cd centerModule
python -m pip install -r tools/requirements.txt
python tools/ble_provision.py --module-id node-001 --upstream-ssid CenterBackhaul --upstream-pass changeme123 --center-url http://localhost:8080
```

Optional args:

- `--address <BLE_MAC>` skip BLE scan and connect directly
- `--ap-ssid <name>`
- `--ap-pass <password>`
- `--scan-timeout <seconds>`

## Firmware Build/Flash (Edge Module)

```bash
cd edgeModule
python -m platformio run -e portenta_c33
python -m platformio run -e portenta_c33 -t upload
python -m platformio device monitor -b 115200
```

For board-specific details, see:

- `edgeModule/README.md`

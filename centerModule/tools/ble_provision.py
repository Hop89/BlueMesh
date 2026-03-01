import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request

from bleak import BleakClient, BleakScanner

SERVICE_UUID = "7f8f0100-1b22-4f6c-a133-8f0f9a2e1001"
CONFIG_CHAR_UUID = "7f8f0101-1b22-4f6c-a133-8f0f9a2e1001"
STATUS_CHAR_UUID = "7f8f0102-1b22-4f6c-a133-8f0f9a2e1001"


def fetch_token(center_url: str, module_id: str) -> str:
    url = f"{center_url.rstrip('/')}/api/provision/token"
    payload = json.dumps({"moduleId": module_id}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["token"]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"failed to fetch token from {url}: {exc}") from exc


async def resolve_device(module_id: str, explicit_address: str | None, scan_timeout: float):
    if explicit_address:
        return explicit_address

    devices = await BleakScanner.discover(timeout=scan_timeout)
    expected_name = f"BlueMesh {module_id}".lower()

    for dev in devices:
        name = (dev.name or "").lower()
        if expected_name in name:
            return dev.address

    raise RuntimeError(f"no BLE device found for module '{module_id}'.")


def build_payload(args, token: str) -> str:
    ap_ssid = args.ap_ssid or f"BlueMesh-{args.module_id}"
    ap_pass = args.ap_pass or "changeme123"
    parts = {
        "moduleId": args.module_id,
        "upstreamSsid": args.upstream_ssid,
        "upstreamPass": args.upstream_pass,
        "token": token,
        "apSsid": ap_ssid,
        "apPass": ap_pass,
    }
    return ";".join(f"{k}={v}" for k, v in parts.items())


async def provision(args):
    token = fetch_token(args.center_url, args.module_id)
    address = await resolve_device(args.module_id, args.address, args.scan_timeout)
    payload = build_payload(args, token)

    print(f"Using device: {address}")
    async with BleakClient(address) as client:
        services = await client.get_services()
        if SERVICE_UUID.lower() not in {s.uuid.lower() for s in services}:
            raise RuntimeError("target device does not expose BlueMesh provisioning service UUID")

        await client.write_gatt_char(CONFIG_CHAR_UUID, payload.encode("utf-8"), response=True)
        status = await client.read_gatt_char(STATUS_CHAR_UUID)
        print("Provisioning status:", status.decode("utf-8", errors="replace"))


def parse_args():
    parser = argparse.ArgumentParser(description="Provision BlueMesh edge module over BLE using bleak")
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--upstream-ssid", required=True)
    parser.add_argument("--upstream-pass", required=True)
    parser.add_argument("--center-url", default="http://localhost:8080")
    parser.add_argument("--address", help="Explicit BLE address (skip discovery)")
    parser.add_argument("--ap-ssid")
    parser.add_argument("--ap-pass")
    parser.add_argument("--scan-timeout", type=float, default=8.0)
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        asyncio.run(provision(args))
    except Exception as exc:  # noqa: BLE001
        print(f"Provisioning failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

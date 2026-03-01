import argparse
import asyncio

from bleak import BleakClient, BleakScanner

RELAY_SERVICE_UUID = "7f8f0200-1b22-4f6c-a133-8f0f9a2e1001"
RELAY_OUT_CHAR_UUID = "7f8f0202-1b22-4f6c-a133-8f0f9a2e1001"


async def resolve_device(module_id: str, explicit_address: str | None, scan_timeout: float) -> str:
    if explicit_address:
        return explicit_address

    devices = await BleakScanner.discover(timeout=scan_timeout)
    expected_name = f"BlueMesh {module_id}".lower()
    for dev in devices:
        if expected_name in (dev.name or "").lower():
            return dev.address

    raise RuntimeError(f"No BLE device found for module '{module_id}'")


def parse_seq(payload: str) -> int:
    for part in payload.split(";"):
        if part.startswith("seq="):
            try:
                return int(part.split("=", 1)[1])
            except ValueError:
                return -1
    return -1


async def listen(args):
    address = await resolve_device(args.module_id, args.address, args.scan_timeout)
    print(f"Listening on device: {address}")

    async with BleakClient(address) as client:
        services = client.services
        if not services:
            services = await client.get_services()

        if RELAY_SERVICE_UUID.lower() not in {s.uuid.lower() for s in services}:
            raise RuntimeError("Relay service UUID not found on device")

        last_seq = -1

        while True:
            raw = await client.read_gatt_char(RELAY_OUT_CHAR_UUID)
            text = raw.decode("utf-8", errors="replace")
            seq = parse_seq(text)
            if seq > last_seq:
                print(text)
                last_seq = seq
            await asyncio.sleep(args.poll_interval)


def parse_args():
    parser = argparse.ArgumentParser(description="Receive relayed messages from Portenta BLE")
    parser.add_argument("--module-id", default="node-001")
    parser.add_argument("--address", help="Explicit BLE address")
    parser.add_argument("--scan-timeout", type=float, default=8.0)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(listen(args))


if __name__ == "__main__":
    main()

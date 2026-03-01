import argparse
import asyncio

from bleak import BleakClient, BleakScanner

RELAY_SERVICE_UUID = "7f8f0200-1b22-4f6c-a133-8f0f9a2e1001"
RELAY_IN_CHAR_UUID = "7f8f0201-1b22-4f6c-a133-8f0f9a2e1001"
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


async def send_message(args):
    address = await resolve_device(args.module_id, args.address, args.scan_timeout)
    payload = f"from={args.sender};msg={args.message}"

    print(f"Using device: {address}")
    async with BleakClient(address) as client:
        services = client.services
        if not services:
            services = await client.get_services()

        if RELAY_SERVICE_UUID.lower() not in {s.uuid.lower() for s in services}:
            raise RuntimeError("Relay service UUID not found on device")

        await client.write_gatt_char(RELAY_IN_CHAR_UUID, payload.encode("utf-8"), response=True)
        relay_state = await client.read_gatt_char(RELAY_OUT_CHAR_UUID)
        print("Relay state:", relay_state.decode("utf-8", errors="replace"))


def parse_args():
    parser = argparse.ArgumentParser(description="Send a message to another computer through Portenta BLE relay")
    parser.add_argument("--module-id", default="node-001")
    parser.add_argument("--address", help="Explicit BLE address")
    parser.add_argument("--sender", default="pc-a")
    parser.add_argument("--message", required=True)
    parser.add_argument("--scan-timeout", type=float, default=8.0)
    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(send_message(args))


if __name__ == "__main__":
    main()

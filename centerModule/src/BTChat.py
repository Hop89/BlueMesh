import argparse
import asyncio

from bleak import BleakClient, BleakScanner

RELAY_SERVICE_UUID = "7f8f0200-1b22-4f6c-a133-8f0f9a2e1001"
RELAY_IN_CHAR_UUID = "7f8f0201-1b22-4f6c-a133-8f0f9a2e1001"
RELAY_OUT_CHAR_UUID = "7f8f0202-1b22-4f6c-a133-8f0f9a2e1001"


def decode_payload(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


async def resolve_device(module_id: str, explicit_address: str | None, scan_timeout: float) -> str:
    if explicit_address:
        return explicit_address

    devices = await BleakScanner.discover(timeout=scan_timeout)
    expected_name = f"BlueMesh {module_id}".lower()
    for dev in devices:
        if expected_name in (dev.name or "").lower():
            return dev.address

    raise RuntimeError(f"No BLE device found for module '{module_id}'")


async def chat_session(args):
    address = await resolve_device(args.module_id, args.address, args.scan_timeout)

    async def on_notify(_handle: int, data: bytearray):
        print(f"\n[relay] {decode_payload(bytes(data))}")

    print(f"Connecting to {address}...")
    async with BleakClient(address, timeout=args.connect_timeout) as client:
        services = client.services
        if not services:
            services = await client.get_services()

        if RELAY_SERVICE_UUID.lower() not in {s.uuid.lower() for s in services}:
            raise RuntimeError("Relay service UUID not found on device")

        await client.start_notify(RELAY_OUT_CHAR_UUID, on_notify)
        print("Connected. Type a message and press Enter. Use /quit to exit.")

        while True:
            line = await asyncio.to_thread(input, "")
            line = line.strip()
            if not line:
                continue
            if line.lower() in {"/quit", "/exit"}:
                break

            payload = f"from={args.sender};msg={line}"
            await client.write_gatt_char(RELAY_IN_CHAR_UUID, payload.encode("utf-8"), response=True)

        await client.stop_notify(RELAY_OUT_CHAR_UUID)


async def run_with_retries(args):
    for attempt in range(1, args.retries + 1):
        try:
            await chat_session(args)
            return
        except Exception as exc:  # noqa: BLE001
            if attempt == args.retries:
                raise RuntimeError(f"chat failed after {args.retries} attempts: {exc}") from exc
            print(f"connect attempt {attempt} failed: {exc}")
            await asyncio.sleep(args.retry_delay)


def parse_args():
    parser = argparse.ArgumentParser(description="Interactive two-computer BLE chat via Portenta relay")
    parser.add_argument("--module-id", default="node-001")
    parser.add_argument("--address", help="Explicit BLE address")
    parser.add_argument("--sender", required=True)
    parser.add_argument("--scan-timeout", type=float, default=8.0)
    parser.add_argument("--connect-timeout", type=float, default=6.0)
    parser.add_argument("--retries", type=int, default=8)
    parser.add_argument("--retry-delay", type=float, default=0.75)
    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(run_with_retries(args))


if __name__ == "__main__":
    main()
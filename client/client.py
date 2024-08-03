from bleak import BleakScanner
import asyncio

async def run():
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Discovered device: {device.name} ({device.address})")

# Run the discovery
asyncio.run(run())
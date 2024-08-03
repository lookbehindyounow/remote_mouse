from bleak import BleakScanner

async def run():
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Discovered device: {device.name} ({device.address})")

# Run the discovery
import asyncio
asyncio.run(run())

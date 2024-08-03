from bleak import BleakScanner
import asyncio

async def run():
    devices=await BleakScanner.discover() # ble scanner to find the gatt server
    for device in devices:
        print(f"Discovered device: {device.name} at {device.address}")

asyncio.run(run())
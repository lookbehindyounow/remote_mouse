from bleak import BleakScanner, BleakClient
import asyncio
from struct import unpack

async def output(characteristic,data): # can maybe be lambda again once working
    print("(----------------------------)")
    print(type(data))

async def connect(address):
    async with BleakClient(address) as client:
        print()
        await client.connect()
        if client.is_connected:
            print("connected to remote_mouse server")
            # services=await client.get_services()
            for service in client.services:
                print(f"Service UUID: {service.uuid}")
                format=["d","b","b","b"] # first will be double rest will be 8-bit int
                for i in range(4):
                    characteristic=service.characteristics[i]
                    print(f"Characteristic UUID: {characteristic.uuid}")
                    print(f"Characteristic properties: {characteristic.properties}")
                    value=await client.read_gatt_char(characteristic.uuid)
                    print(format[i])
                    print(unpack(format[i],value)[0])
                    await client.start_notify(characteristic.uuid,output)
            try:
                while True:
                    await update(client)
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                for service in client.services:
                    for characteristic in service.characteristics:
                        await client.stop_notify(characteristic.uuid)
                await client.disconnect()
                print("disconnected")
        else:
            print("failed to connect to remote_mouse server")

async def update(client):
    for service in client.services:
        print(unpack("d",await client.read_gatt_char(service.characteristics[0].uuid))[0])

async def run():
    devices=await BleakScanner.discover()
    found=False
    for device in devices:
        print(f"found {device.name} at {device.address}")
        if device.name=="remote_mouse":
            found=True
            await connect(device.address)
    if not found:
        print("can't find remote_mouse server")

asyncio.run(run())
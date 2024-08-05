from bleak import BleakScanner, BleakClient # for BLE scanning/client
from asyncio import run, create_task, gather # a lot of BLE stuff is asynchronous
from struct import unpack # to turn byte arrays into other types

async def scan(): # scan for devices
    devices=await BleakScanner.discover() # scan
    found=False
    for device in devices:
        print(f"found {device.name} at {device.address}")
        if device.name=="remote_mouse":
            found=True
            await connect(device.address)
            break
    if not found:
        print("can't find remote_mouse server")

async def connect(address): # connect to remote-mouse gatt server
    async with BleakClient(address) as client: # create client
        await client.connect() # connect
        # await client.disconnect() to disconnect
        if client.is_connected:
            print("connected to remote_mouse server")
            service=list(client.services)[0]
            print(f"service UUID: {service.uuid}")
            formats=["d","d","b","b"] # first two are doubles other two are bytes
            tasks=[create_task(subscribe(client,service.characteristics[i],formats[i])) for i in range(4)]
            await gather(*tasks)
        else:
            print("failed to connect to remote_mouse server")

async def subscribe(client,characteristic,format):
    print(f"subscribed to characteristic with UUID: {characteristic.uuid}")
    await client.start_notify(characteristic,lambda characteristic,data: print(unpack(format,data)[0]))
    # await client.stop_notify(uuid) to stop

run(scan())
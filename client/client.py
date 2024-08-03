from bleak import BleakScanner, BleakClient
import asyncio

uuids=[f"0000450{i+1}-0000-1000-8000-00805f9b34fb" for i in range(4)]
async def connect(address):
    async with BleakClient(address) as client:
        print()
        await client.connect()
        if client.is_connected:
            print("connected to remote_mouse server")
            # for uuid in uuids:
            #     await client.start_notify(uuid,lambda sender,data: print(data))
            try:
                while True:
                    print(1)
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                for uuid in uuids:
                    await client.stop_notify(uuid)
                await client.disconnect()
                print("disconnected")
        else:
            print("failed to connect to remote_mouse server")

async def run():
    servers=await BleakScanner.discover()
    found=False
    for server in servers:
        print(f"found {server.name} at {server.address}")
        if server.name=="remote_mouse":
            found=True
            await connect(server.address)
    if not found:
        print("can't find remote_mouse server")

asyncio.run(run())
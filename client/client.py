from bleak import BleakScanner, BleakClient # for BLE scanning/client
from asyncio import run as async_run, create_task, gather # a lot of BLE stuff is asynchronous
from pyautogui import moveRel, click, rightClick, press # to control laptop
from subprocess import run as sub_run
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
            formats=["d","d","B","B"] # first two are doubles other two are unsigned bytes
            tasks=[create_task(subscribe(client,service.characteristics[i],formats[i])) for i in range(4)]
            await gather(*tasks)
        else:
            print("failed to connect to remote_mouse server")

async def subscribe(client,characteristic,format):
    print(f"subscribed to characteristic with UUID: {characteristic.uuid}")
    await client.start_notify(characteristic,
        lambda characteristic,data,format=format: handle_input(characteristic.uuid[7],data,format))
    # await client.stop_notify(uuid) to stop

def handle_input(char_i,data,format):
    input=unpack(format,data)[0]
    print(char_i,input)
    match int(char_i): # which characteristic
        case 1: # mouse x
            moveRel(input,0)
        case 2: # mouse y
            moveRel(0,-input) # y inverted cause mac screen coords start in top left
        case 3: # buttons
            match input:
                case 0: # left mouse
                    click()
                case 1: # right mouse
                    rightClick()
                case 2: # left arrow
                    press("left")
                case 3: # right arrow
                    press("right")
        case 4: # volume
            sub_run(["osascript","-e",f"set volume output volume {input/2.55}"]) # runs applescript

async_run(scan())
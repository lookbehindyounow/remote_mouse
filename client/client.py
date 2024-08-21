from bleak import BleakScanner, BleakClient # for BLE scanning/client
from asyncio import run as async_run, create_task, gather, Lock, sleep # a lot of BLE stuff is asynchronous
from pynput.mouse import Controller as Mouse, Button # to control laptop
from pynput.keyboard import Controller as Keyboard, Key
from struct import unpack # to turn byte arrays into other types
from time import time

class Client:
    def __init__(self):
        self.buffer=None
        self.mouse=Mouse()
        self.keyboard=Keyboard()
        self.mouse_down=False

    async def scan(self): # scan for devices
        devices=await BleakScanner.discover() # scan
        found=False
        for device in devices:
            print(f"found {device.name} at {device.address}")
            if device.name=="remote_mouse":
                found=True
                await self.connect(device.address)
                break
        if not found:
            print("can't find remote_mouse server")

    async def connect(self,address): # connect to remote-mouse gatt server
            self.bclient=BleakClient(address) # create client
            await self.bclient.connect() # connect
            # await self.bclient.disconnect() to disconnect
            if self.bclient.is_connected:
                print("connected to remote_mouse server")
                service=list(self.bclient.services)[0]
                print(f"service UUID: {service.uuid}")
                self.characteristic=service.characteristics[0]
                create_task(self.handle_input())
                await self.subscribe()
            else:
                print("failed to connect to remote_mouse server")

    async def subscribe(self):
        print(f"subscribed to characteristic with UUID: {self.characteristic.uuid}")
        await self.bclient.start_notify(self.characteristic,
            lambda characteristic,data: self.set_buffer(data))
        # await self.bclient.stop_notify(uuid) to stop

    def set_buffer(self,data):
        self.buffer=data

    async def handle_input(self):
        while True:
            if self.buffer:
                data=self.buffer
                self.buffer=None # clear buffer first thing to avoid clearing new unhandled input
                input=unpack("H",data)[0] # 16 bits to int
                print(f"{input:016b}")
                #          |dx|       * 1|-1 depending on sign bit
                dx=((input&30720)>>11)*[1,-1][(input&32768)>>15]
                dy=((input&960)>>6)*[1,-1][(input&1024)>>10]
                self.mouse.move(dx,dy)
                # if button bit is 1 press, if 0 release
                if input&32 and not self.mouse_down:
                    self.mouse.press(Button.left)
                    self.mouse_down=True
                elif not input&32 and self.mouse_down:
                    self.mouse.release(Button.left)
                    self.mouse_down=False
                self.mouse.press(Button.right) if input&16 else self.mouse.release(Button.right)
                self.keyboard.press(Key.left) if input&8 else self.keyboard.release(Key.left)
                self.keyboard.press(Key.right) if input&4 else self.keyboard.release(Key.right)
                self.keyboard.press(Key.media_volume_up) if input&2 else self.keyboard.release(Key.media_volume_up)
                self.keyboard.press(Key.media_volume_down) if input&1 else self.keyboard.release(Key.media_volume_down)
            await sleep(0)

async_run(Client().scan())
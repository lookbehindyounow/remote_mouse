from bleak import BleakScanner, BleakClient # for BLE scanning/client
from asyncio import run as async_run, create_task, gather, Lock, sleep # a lot of BLE stuff is asynchronous
from pynput.mouse import Controller as Mouse, Button # to control laptop
from pynput.keyboard import Controller as Keyboard, Key
from struct import unpack # to turn byte arrays into other types
from time import time

class Client:
    def __init__(self):
        self.buffer=None
        self.mouse_down=False
        self.mouse=Mouse()
        self.keyboard=Keyboard()

    async def scan(self,target): # scan for devices
        devices=await BleakScanner.discover() # scan, this part takes a while
        for device in devices:
            if device.name==target:
                return device
        print(f"can't find {target} server")
        return None

    async def connect(self,server): # connect to remote-mouse gatt server
        self.bclient=BleakClient(server.address) # create client
        await self.bclient.connect() # connect to server, this part takes a while
        # await self.bclient.disconnect() to disconnect
        if self.bclient.is_connected:
            print(f"connected to {server.name} server\n\tServices:")
            services=list(self.bclient.services)
            [print(f"\t\tservice UUID: {service.uuid}") for service in services]
            [[print(f"\t\t\tcharacteristic UUID: {characteristic.uuid}") for characteristic in service.characteristics] for service in services]
            return services
        print(f"failed to connect to {server.name} server")
        return None

    async def subscribe(self,characteristics):
        print()
        [print(f"subscribing to characteristic with UUID: {characteristic.uuid}") for characteristic in characteristics]
        await gather(*[create_task(self.bclient.start_notify(characteristic,self.set_buffer)) for characteristic in characteristics]) # runs until stopped

    def set_buffer(self,characteristic,data):
        self.buffer=data

    async def handle_input(self):
        print("handling")
        while True:
            if self.buffer:
                data=self.buffer
                self.buffer=None # clear buffer first thing to avoid clearing new unhandled input
                input=unpack("H",data)[0] # 16 bits to int
                # print(f"{input:016b}")
                #  ┌-------|dx|------┐* 1|-1 depending on sign bit
                dx=((input&30720)>>11)*[1,-1][(input&32768)>>15]
                dy=((input&960)>>6)*[1,-1][(input&1024)>>10]
                self.mouse.move(dx,dy)
                # if left mouse bit is 1 & mouse isn't already down, press
                if input&32 and not self.mouse_down:
                    self.mouse.press(Button.left)
                    self.mouse_down=True
                # if left mouse bit is 0 & mouse is currently down, release
                elif not input&32 and self.mouse_down:
                    self.mouse.release(Button.left)
                    self.mouse_down=False
                # other button bits can just be set every frame cause the functionality of holding them is not as important
                self.mouse.press(Button.right) if input&16 else self.mouse.release(Button.right)
                self.keyboard.press(Key.left) if input&8 else self.keyboard.release(Key.left)
                self.keyboard.press(Key.right) if input&4 else self.keyboard.release(Key.right)
                self.keyboard.press(Key.media_volume_up) if input&2 else self.keyboard.release(Key.media_volume_up)
                self.keyboard.press(Key.media_volume_down) if input&1 else self.keyboard.release(Key.media_volume_down)
            await sleep(0.01)
    
    async def run(self):
        while True:
            try:
                remote_mouse_server=await self.scan("remote_mouse")
                if remote_mouse_server:
                    remote_mouse_services=await self.connect(remote_mouse_server)
                    await gather(self.subscribe(remote_mouse_services[0].characteristics),self.handle_input())
            except Exception as error:
                print()
                print("error:",error)
            print("starting again")
            print("=====================================")
            print()

async_run(Client().run())
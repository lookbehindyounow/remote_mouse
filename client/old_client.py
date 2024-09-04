from bleak import BleakScanner, BleakClient # for BLE scanning/client
from asyncio import run as async_run, create_task, gather, sleep # a lot of BLE stuff is asynchronous
from struct import unpack # to turn byte arrays into other types
from pynput.mouse import Controller as Mouse, Button # to control laptop
from pynput.keyboard import Controller as Keyboard, Key
from time import time # for timing connection duration & update frequency

class Client:
    def __init__(self):
        self.buffer=None
        self.connection_time=None
        self.prev_update=None
        self.mouse=Mouse()
        self.mouse.down=False
        self.keyboard=Keyboard()

    async def scan(self,target):
        print("Scanning...")
        devices=await BleakScanner.discover() # point of scan, this part takes a while
        for device in devices:
            if device.name==target:
                return device
        print(f"Can't find {target} server")
        return None

    async def connect(self,server):
        self.bclient=BleakClient(server.address)
        print(f"Connecting to {server.name} server...")
        await self.bclient.connect() # point of connection, also takes a while
        # await self.bclient.disconnect() to disconnect
        if self.bclient.is_connected:
            self.connection_time=time()
            print(f"Connected to {server.name} server\nServices:")
            services=list(self.bclient.services)
            for service in services:
                print(f"  Service UUID: {service.uuid}\n  Characteristics:")
                for characteristic in service.characteristics:
                    print(f"    Characteristic UUID: {characteristic.uuid}")
            return services
        print(f"Failed to connect to {server.name} server")
        return None

    async def subscribe(self,characteristics):
        print()
        [print(f"Subscribing to characteristic with UUID: {characteristic.uuid}") for characteristic in characteristics]
        await gather(*[self.bclient.start_notify(characteristic,self.set_buffer) for characteristic in characteristics])
        # runs until disconnected or bclient.stop_notify(characteristic.uuid)

    def set_buffer(self,characteristic,data):
        self.buffer=data
        # update_time=time()
        # if self.prev_update: print(f"buffer updated after {update_time-self.prev_update}s")
        # self.prev_update=update_time

    async def handle_input(self):
        print("Handling input...")
        while True:
            if self.buffer:
                data=self.buffer
                self.buffer=None # clear buffer first thing to avoid clearing new unhandled input
                input=unpack("H",data)[0] # 16 bits to int
                print(f"{input:016b}")
                #  ┌-------|dx|------┐* 1|-1 depending on sign bit
                dx=((input&30720)>>11)*[1,-1][(input&32768)>>15]
                dy=((input&960)>>6)*[1,-1][(input&1024)>>10]
                self.mouse.move(dx,dy)
                # if left mouse bit is 1 & mouse isn't already down, press
                if input&32 and not self.mouse.down:
                    self.mouse.press(Button.left)
                    self.mouse.down=True
                # if left mouse bit is 0 & mouse is currently down, release
                elif not input&32 and self.mouse.down:
                    self.mouse.release(Button.left)
                    self.mouse.down=False
                # other button bits can just be set every frame cause the functionality of holding them is not as important
                self.mouse.press(Button.right) if input&16 else self.mouse.release(Button.right)
                self.keyboard.press(Key.left) if input&8 else self.keyboard.release(Key.left)
                self.keyboard.press(Key.right) if input&4 else self.keyboard.release(Key.right)
                self.keyboard.press(Key.media_volume_up) if input&2 else self.keyboard.release(Key.media_volume_up)
                self.keyboard.press(Key.media_volume_down) if input&1 else self.keyboard.release(Key.media_volume_down)
            await sleep(0.01)
    
    async def stay_awake(self,dummy_characteristic_uuid):
        while True:
            print(f"reading characteristic {dummy_characteristic_uuid} to stay awake...")
            dummy_characteristic_data=await self.bclient.read_gatt_char(dummy_characteristic_uuid)
            dummy_characteristic_value=unpack("H",dummy_characteristic_data)[0]
            print(f"characteristic {dummy_characteristic_uuid} value: {dummy_characteristic_value:016b}")
            await self.bclient.write_gatt_char(dummy_characteristic_uuid,dummy_characteristic_data)
            await sleep(2)
    
    async def run(self):
        while True:
            try:
                remote_mouse_server=await self.scan("remote_mouse")
                if remote_mouse_server:
                    remote_mouse_services=await self.connect(remote_mouse_server)
                    await gather(self.subscribe(remote_mouse_services[0].characteristics),self.handle_input(),self.stay_awake(remote_mouse_services[0].characteristics[0].uuid))
                    # await gather(self.subscribe(remote_mouse_services[0].characteristics),self.handle_input())
                    # await self.stay_awake(remote_mouse_services[0].characteristics[0].uuid)
            except Exception as error:
                print()
                if self.connection_time:
                    print(f"Connected for {time()-self.connection_time}s") # consistently disconnects after 30s when subscribed
                    self.connection_time=None
                if isinstance(error,TimeoutError):
                    print("Timed out")
                else:
                    print("Error:",error)
            print("Starting again")
            print("=====================================\n")

async_run(Client().run())
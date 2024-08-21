from bleak import BleakScanner, BleakClient # for BLE scanning/client
from asyncio import run as async_run, create_task, gather, Lock, sleep # a lot of BLE stuff is asynchronous
from pyautogui import moveRel, click, rightClick, press # to control laptop
from subprocess import run as sub_run
from struct import unpack # to turn byte arrays into other types

class Client:
    def __init__(self):
        self.formats=["d","d","B","B"] # first two characteristics are doubles other two are unsigned bytes
        self.buffer=[None]*4
        self.locks=[Lock() for i in range(4)]

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
                self.characteristics=service.characteristics
                subscriptions=[create_task(self.subscribe(i)) for i in range(4)]
                create_task(self.monitor_buffer())
                await gather(*subscriptions)
            else:
                print("failed to connect to remote_mouse server")

    async def subscribe(self,char_i):
        print(f"subscribed to characteristic with UUID: {self.characteristics[char_i].uuid}")
        await self.bclient.start_notify(self.characteristics[char_i],
            lambda characteristic,data: self.set_buffer(int(characteristic.uuid[7])-1,data))
        # await self.bclient.stop_notify(uuid) to stop

    def set_buffer(self,char_i,data):
        self.buffer[char_i]=data

    async def monitor_buffer(self): # try running different inputs concurrently with 4 locks vs 1 at a time with 1 lock
        while True:
            for i in range(3):
                if i==0:
                    data=self.buffer[:2] # get mouse x & y together (try as one characteristic)
                    if data!=[None,None]: # if either buffer has data
                        create_task(self.handle_input(0,data)) # send both with i=0
                        self.buffer[:2]=[None,None] # clear buffer
                else:
                    data=self.buffer[i+1] # get buttons|volume
                    if data!=None: # if buffer has data
                        create_task(self.handle_input(i,data)) # send data
                        self.buffer[i+1]=None # clear buffer
            await sleep(0.01)

    async def handle_input(self,i,data):
        async with self.locks[i]: # 4 different locks
            print(i,data)
            match i: # which characteristic
                case 0: # mouse x/y
                    input=[5*unpack("d",datum)[0] if datum else 0 for datum in data]
                    print(input)
                    moveRel(*input)
                case 1: # buttons
                    input=unpack("B",data)[0]
                    print(input)
                    match input:
                        case 0: # left mouse
                            click()
                        case 1: # right mouse
                            rightClick()
                        case 2: # left arrow
                            press("left")
                        case 3: # right arrow
                            press("right")
                case 2: # volume
                    input=unpack("B",data)[0]
                    print(input)
                    sub_run(["osascript","-e",f"set volume output volume {input/2.55}"]) # runs applescript

async_run(Client().scan())
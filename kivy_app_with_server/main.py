from jnius import autoclass, PythonJavaClass, java_method # this allows us to work with java classes so we can access android bluetooth functionality
from struct import pack # to turn variables into byte arrays
from math import floor # for button pos calc
from time import time # for notification frequency logging

# UI stuff
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.metrics import dp
from kivy.clock import Clock

# need java classes to do android stuff
try: # but these would all throw errors when testing UI on the laptop, hence "try"
    from android.permissions import request_permissions, Permission # this is not a real python library
    # it's handled at compile-time & is only here to ask runtime permissions, which I'm not yet 100% sure we need

    # java context stuff
    Context=autoclass('android.content.Context')
    PythonActivity=autoclass('org.kivy.android.PythonActivity')

    # bluetooth
    BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothManager=autoclass('android.bluetooth.BluetoothManager') # may not be necessary, never explicitly used but is used

    # gatt server
    GattService=autoclass('android.bluetooth.BluetoothGattService')
    GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')
    GattDescriptor=autoclass('android.bluetooth.BluetoothGattDescriptor')
    GattCallback=autoclass('com.remotemouse.GattCallback') # need a gatt server callback object & BluetoothGattServerCallback is an abstract class
    BluetoothGattServer=autoclass('android.bluetooth.BluetoothGattServer') # may not be necessary, never explicitly used but is used
    BluetoothGattServerCallback=autoclass('android.bluetooth.BluetoothGattServerCallback') # may not be necessary, is extended by GattCallback
    BluetoothDevice=autoclass('android.bluetooth.BluetoothDevice')

    # advertising
    AdCallback=autoclass('com.remotemouse.AdCallback') # need an advertise callback object & AdvertiseCallback is an abstract class
    AdvertiseSettings=autoclass('android.bluetooth.le.AdvertiseSettings')
    AdvertiseSettingsBuilder=autoclass('android.bluetooth.le.AdvertiseSettings$Builder')
    AdvertiseData=autoclass('android.bluetooth.le.AdvertiseData')
    AdvertiseDataBuilder=autoclass('android.bluetooth.le.AdvertiseData$Builder')
    AdvertiseCallback=autoclass('android.bluetooth.le.AdvertiseCallback') # may not be necessary, is extended by AdCallback
    BluetoothLeAdvertiser=autoclass('android.bluetooth.le.BluetoothLeAdvertiser') # may not be necessary, never explicitly used but is used
    ParcelUUID=autoclass("android.os.ParcelUuid") # UUIDs need to be parcel UUIDs for advertising?
except: # so importing the android classes don't throw errors when testing ui on my mac
    pass

UUID=autoclass('java.util.UUID') # data type
def uuid(id): # bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

class JavaMessenger(PythonJavaClass):
    __javainterfaces__=["com/remotemouse/IJavaMessenger"]
    __javacontext__="app"
    def __init__(self,app):
        self.app=app

    @java_method("(Ljava/lang/String;)V")
    def callInPython(self,message):
        self.app.update_message(1,message)

class RemoteMouseApp(App): # app
    def __init__(self,**kwargs):
        self.start_time=time()
        super().__init__(**kwargs) # init kivy app stuff
        self.message="\n\n" # effectively a 3 section log/status thing displayed on screen for debug

        try: # creating service and characteristics for input data stream, android only hence "try"
            self.service=GattService(uuid(4500),GattService.SERVICE_TYPE_PRIMARY) # service
            self.update_message(1,"made service")

            self.characteristic=GattCharacteristic(uuid(4500), # characteristic
                GattCharacteristic.PROPERTY_NOTIFY| # for characteristic to support BLE notifications
                GattCharacteristic.PROPERTY_READ, # allow client to read characteristic's value - may not need with notifications
                GattCharacteristic.PERMISSION_READ| # allow client to read characteristic's value - may not need with notifications
                GattCharacteristic.PERMISSION_WRITE) # experimenting with Client.stay_awake()
            self.update_message(1,f"made characteristic with UUID: {uuid(4500)}")

            self.characteristic.setValue(pack("H",0)) # initial value, pack into bye array
            self.update_message(1,"set initial value")

            # Client Characteristic Configuration Descriptor - unsure if it needs PERMISSION_READ
            descriptor=GattDescriptor(uuid(2902),GattDescriptor.PERMISSION_READ|GattDescriptor.PERMISSION_WRITE)
            # the client writes to this^ descriptor to request notifications & it has to have that specific UUID
            descriptor.setValue(GattDescriptor.ENABLE_NOTIFICATION_VALUE) # may not be necessary 
            self.update_message(1,"made CCCD")
            self.characteristic.addDescriptor(descriptor) # add descriptor to characteristic
            self.update_message(1,"added CCCD to characteristic")

            self.service.addCharacteristic(self.characteristic)
            self.update_message(1,"added characteristic to service")

        except Exception as error:
            self.update_message(2,error) # log error
    
    def update_message(self,part,new): # update section of log/status thing displayed on screen for debug
        # 3 lines, top is data to send as byte[2] characteristic, middle is just general logs & bottom is errors
        contents=self.message.split("\n")
        contents[part]=new
        self.message=f"{contents[0]}\n{contents[1]}\n{contents[2]}"
        print(f"HERE{part}",new) # log message update in console
        try:
            self.ui.screen_logs.text=self.message
        except AttributeError:
            pass

    def setup(self):
        try:
            # may not need to request permissions at runtime but this is where it happens
            request_permissions([Permission.BLUETOOTH,Permission.BLUETOOTH_ADMIN,Permission.ACCESS_FINE_LOCATION])

            self.adapter=BluetoothAdapter.getDefaultAdapter() # getting android's bluetooth adapter
            self.update_message(1,"got bluetooth adapter")

            if not self.adapter.isEnabled(): # check if bluetooth's on
                self.update_message(1,"bluetooth disabled")
                return
            self.update_message(1,"bluetooth enabled")

            self.adapter.setName("remote_mouse") # for client to recognise - is this the best way?
            self.update_message(1,"set name")

            app_context=PythonActivity.mActivity
            self.update_message(1,"got app context")

            bluetooth_manager=app_context.getSystemService(Context.BLUETOOTH_SERVICE) # getting android's bluetooth manager
            self.update_message(1,"got bluetooth manager")

            self.java_messenger=JavaMessenger(self)
            self.gatt_callback=GattCallback(self.java_messenger) # callback object for gatt server
            self.gatt_server=bluetooth_manager.openGattServer(app_context,self.gatt_callback) # create gatt server
            self.gatt_callback.setServer(self.gatt_server) # the callback needs the server to respond to read requests
            self.update_message(1,"created server")

            self.gatt_server.addService(self.service) # add previously defined service with characteristics to server
            self.update_message(1,"added service to server")

            self.advertise() # make discoverable

        except Exception as error:
            self.update_message(2,error) # log error
    
    def advertise(self): # make discoverable
        try:
            bluetooth_advertiser=self.adapter.getBluetoothLeAdvertiser() # getting android's BLE advertiser
            self.update_message(1,"got BLE advertiser")

            settings_builder=AdvertiseSettingsBuilder() # can we instantiate AdvertiseSettings without the builder?
            # options: ADVERTISE_MODE_LOW_LATENCY, ADVERTISE_MODE_BALANCED, ADVERTISE_MODE_BALANCED
            settings_builder.setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            # options: ADVERTISE_TX_POWER_HIGH, ADVERTISE_TX_POWER_MEDIUM, ADVERTISE_TX_POWER_LOW, ADVERTISE_TX_POWER_ULTRA_LOW
            settings_builder.setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            settings_builder.setConnectable(True)
            settings=settings_builder.build() # settings object for advertiser
            self.update_message(1,"built advertise settings object")

            data_builder=AdvertiseDataBuilder() # can we instantiate AdvertiseData without the builder?
            data_builder.setIncludeDeviceName(True).addServiceUuid(ParcelUUID(uuid(4500)))
            data=data_builder.build() # data object for advertiser
            self.update_message(1,"built advertise data object")

            self.ad_callback=AdCallback(self.java_messenger) # callback object for advertiser - remember to check logs from this object when debugging
            bluetooth_advertiser.startAdvertising(settings,data,self.ad_callback)
            self.update_message(1,"starting advertiser...")

        except Exception as error:
            self.update_message(2,error) # log error

    def build(self):
        print("HERE3 assigning self.ui")
        self.ui=MainWidget(self)
        return self.ui # give kivy the ui

class MainWidget(BoxLayout): # UI
    def __init__(self,app,**kwargs):
        super().__init__(**kwargs) # init kivy widget stuff
        self.input_buffer=0 # this is where the current input will be written to before it's packaged into 2 bytes & sent
        # self.app=App.get_running_app() # get app
        self.app=app # get app
        self.padding=dp(20)
        self.spacing=dp(10)

        self.mouse_pad=Widget() # to detect touches
        self.mouse_pad.bind(on_touch_down=self.read_mouse,on_touch_move=self.read_mouse) # binding screen touch methods
        self.mouse_pad.bind(on_touch_up=self.reset_mouse)
        self.reset_mouse(None,None)
        self.add_widget(self.mouse_pad)

        self.screen_logs=Label(valign="center") # to display log/status thing for debug
        self.mouse_pad.add_widget(self.screen_logs)
        self.app.update_message(0,f"{self.input_buffer:016b}")
        self.app.update_message(1,"screen logs running")
        Clock.schedule_once(lambda event: self.on_size(None,None)) # initial set label pos

        self.button_container=GridLayout()
        self.buttons=["left mouse","right mouse","left arrow","right arrow","volume up","volume down"] # button text
        for i in range(6): # create buttons
            self.buttons[i]=Button(text=self.buttons[i])
            self.buttons[i].i=i
            self.buttons[i].bind(on_press=self.press,on_release=self.release)
            self.button_container.add_widget(self.buttons[i])
        self.add_widget(self.button_container)

        self.app.setup() # begin bluetooth process - why is this in the widget & not the app?

    def on_size(self,caller,size):
        if self.width>self.height: # landscape
            self.orientation="horizontal"
            self.button_container.clear_widgets()
            self.button_container.rows=2
            # order of buttons is different for landscape
            [self.button_container.add_widget(self.buttons[i]) for i in [0,1,4,2,3,5]]
        else: # portrait
            self.orientation="vertical"
            self.button_container.clear_widgets()
            self.button_container.rows=3
            [self.button_container.add_widget(self.buttons[i]) for i in range(6)]
        # when you rotate your phone it calls on_size before widget positions have updated
        # so moving the log/status thing needs to be scheduled
        Clock.schedule_once(self.place_label)
    
    def place_label(self,dt):
        self.screen_logs.pos=self.mouse_pad.to_parent(0,0,True) # display log/status thing in mouse_pad
        self.screen_logs.size=self.mouse_pad.size
        self.screen_logs.text_size=self.mouse_pad.size
    
    def read_mouse(self,caller,touch): # handle mouse pad input
        if self.mouse_pad.collide_point(*touch.pos): # only if touch pos is within mouse pad pos
            x,y=self.mouse_pad.to_local(*touch.pos,True) # get coords relative to mouse pad origin
            x,y=floor(x),floor(y) # to int (round down to allow for slightly easier micro-movements)
            if self.x0!=None and self.y0!=None: # don't send first touch
                dx=x-self.x0 # get x & y direction (ints)
                dy=y-self.y0

                self.input_buffer&=63 # keep only last 6 bits - wipe pos data (first 10 bits) to 0s
                if dx<0: self.input_buffer|=32768 # bit 1 is sign bit for dx
                if dy>0: self.input_buffer|=1024 # bit 6 is sign bit for dy (inverted cause mac screen coords start in top left)

                dx=min(abs(dx),15) # get x & y direction magnitude capped at 15 (to fit into 4 bits each)
                dy=min(abs(dy),15)
                self.input_buffer|=(dx<<11)|(dy<<6) # put 4 bit representations of dx & dy into places 2-5 & 7-10 respectively

                self.send()
            self.x0,self.y0=x,y # update last position for next frame's direction
    
    def reset_mouse(self,caller,touch): # re-initialise mouse tracking at end of touch
        self.x0,self.y0=None,None
        self.input_buffer&=63 # wipe pos data (first 10 bits) to 0s
    
    def press(self,caller): # handle button press
        self.input_buffer|=(32>>caller.i) # set relevant button bit (positions 11-16) to 1
        self.send()
    
    def release(self,caller): # handle button press
        self.input_buffer&=65535-(32>>caller.i) # set relevant button bit (positions 11-16) to 0
        self.send()
    
    def send(self): # update characteristic & notify client
        self.app.update_message(0,f"{self.input_buffer:016b}") # send input to app logs
        try:
            self.app.characteristic.setValue(pack("H",self.input_buffer)) # package double into byte array for new characteristic values
            device=self.app.gatt_callback.device # client - or most recent client? unsure if callback handles disconnection
            if device: # send notifications only if client connected
                self.app.gatt_server.notifyCharacteristicChanged(device,self.app.characteristic,False)
        except Exception as error:
            self.app.update_message(2,error) # log error

RemoteMouseApp().run() # instantiate & run (initialise & build) app
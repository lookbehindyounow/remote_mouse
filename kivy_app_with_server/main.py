from jnius import autoclass # this allows us to work with java classes so we can access android bluetooth functionality
from struct import pack # to turn variables into byte arrays

# UI stuff
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
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

except:
    pass

UUID=autoclass('java.util.UUID') # data type
def uuid(id): # bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

class RemoteMouseApp(App): # app
    def __init__(self,**kwargs):
        super().__init__(**kwargs) # init kivy app stuff
        self.message="0\n\n" # effectively a 3 section log/status thing displayed on screen for debug
        self.gatt_callback=None # is accessed in update() which is called by MainWidget periodically so needs to be defined

        try: # creating service and characteristics for input data stream, android only hence "try"
            self.service=GattService(uuid(4500),GattService.SERVICE_TYPE_PRIMARY) # service
            self.update_message(1,"made service")

            self.characteristics=[]
            formats=["d","d","b","b"] # mouse x & y are floats, volume is 8-bit int & left/right mouse/arrows can be 4 bits of a byte
            for i in range(4):
                self.characteristics.append(GattCharacteristic(uuid(i+4501), # characteristic
                    GattCharacteristic.PROPERTY_NOTIFY| # for characteristic to support BLE notifications
                    GattCharacteristic.PROPERTY_READ, # allow client to read characteristic's value - may not need with notifications
                    GattCharacteristic.PERMISSION_READ)) # allow client to read characteristic's value - may not need with notifications
                self.update_message(1,f"made characteristic with UUID: {uuid(i+4501)}")

                self.characteristics[i].setValue(pack(formats[i],0)) # initial value, pack into bye array
                self.update_message(1,f"set initial value")

                # Client Characteristic Configuration Descriptor - unsure if it needs PERMISSION_READ
                descriptor=GattDescriptor(uuid(2902),GattDescriptor.PERMISSION_READ|GattDescriptor.PERMISSION_WRITE)
                # the client writes to this^ descriptor to request notifications & it has to have that specific UUID
                descriptor.setValue(GattDescriptor.ENABLE_NOTIFICATION_VALUE) # may not be necessary 
                self.update_message(1,f"made CCCD")
                self.characteristics[i].addDescriptor(descriptor) # add descriptor to characteristic
                self.update_message(1,f"added CCCD to characteristic")

                self.service.addCharacteristic(self.characteristics[i])
                self.update_message(1,f"added characteristic to service")

        except Exception as error:
            self.update_message(2,error) # log error
    
    def update_message(self,part,new): # update section of log/status thing displayed on screen for debug
        # 3 lines, top is 1|0 & flips twice a second to show app isn't frozen, middle is setup status & bottom is error/connection state
        contents=self.message.split("\n")
        contents[part]=str(new)
        self.message=f"{contents[0]}\n{contents[1]}\n{contents[2]}"
        if part: # if it's not the 1|0 flip
            print("HERE1",new) # log message update in console

    def update(self): # called by UI MainWidget to get log/status thing to display on screen for debug
        self.update_message(0,int(not int(self.message[0]))) # also handles the 1|0 flip
        if self.gatt_callback: # if gatt callback object exists yet & isn't still None
            self.update_message(2,self.gatt_callback.message) # update connection state
        return self.message

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

            self.gatt_callback=GattCallback() # callback object for gatt server
            self.gatt_server=bluetooth_manager.openGattServer(app_context,self.gatt_callback) # create gatt server
            self.gatt_callback.addServer(self.gatt_server) # the callback needs the server to respond to read requests
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
            data_builder.setIncludeDeviceName(True)
            data=data_builder.build() # data object for advertiser
            self.update_message(1,"built advertise data object")

            ad_callback=AdCallback() # callback object for advertiser - remember to check logs from this object when debugging
            bluetooth_advertiser.startAdvertising(settings, data, ad_callback)
            self.update_message(1,"started advertising")

        except Exception as error:
            self.update_message(2,error) # log error

    def build(self):
        return MainWidget() # assign UI

class MainWidget(Widget): # UI - currently just displays touch pos & log/status thing on the screen
    def __init__(self,**kwargs):
        super().__init__(**kwargs) # init kivy widget stuff
        self.app=App.get_running_app() # get app
        self.zone=Scatter(do_translation=False,do_rotation=False,do_scale=False) # to detect touches
        self.zone.bind(on_touch_down=self.read_mouse,on_touch_move=self.read_mouse) # binding screen touch methods
        self.out=Label() # to display touch pos
        self.out2=Label(size_hint=(0.9,None)) # to display log/status thing
        self.add_widget(self.zone)
        self.add_widget(self.out)
        self.add_widget(self.out2)
        Clock.schedule_interval(self.update,0.5) # for periodic updates to log/status thing
        self.app.setup() # begin bluetooth process - why is this here?
    
    def read_mouse(self,caller,touch): # on screen touch
        self.out.text=str(touch.pos) # display touch pos
        try:
            self.app.characteristics[0].setValue(pack("d",pos[0])) # package double into byte array for new characteristic values
            self.app.characteristics[1].setValue(pack("d",pos[1]))
            device=self.app.gatt_callback.device # client - or most recent client? unsure if callback handles disconnection
            if device: # if client connected, send notifications
                self.app.gatt_server.notifyCharacteristicChanged(device,self.app.characteristics[0],False)
                self.app.gatt_server.notifyCharacteristicChanged(device,self.app.characteristics[1],False)
        except Exception as error:
            self.app.update_message(2,error) # log error
    
    def on_size(self,size):
        self.out.pos=(self.width/2,self.height/2) # touch pos in middle of screen
        self.out2.pos=(self.width/2,self.height/4) # display below touch pos
    
    def update(self,dt): # update log/status thing
        self.out2.text=self.app.update() # get from app

RemoteMouseApp().run() # instantiate & run (initialise & build) app
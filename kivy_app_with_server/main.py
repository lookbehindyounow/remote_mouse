from jnius import autoclass # this allows us to work with java classes so we can access android bluetooth functionality
from struct import pack

# UI stuff
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.clock import Clock

# need java classes to do android stuff
try:
    from android.permissions import request_permissions, Permission # this is not a real python library
    # it's handled at compile-time & is only here to ask runtime permissions, which I'm not yet 100% sure we need
    Context=autoclass('android.content.Context')
    PythonActivity=autoclass('org.kivy.android.PythonActivity')

    # bluetooth
    BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothManager=autoclass('android.bluetooth.BluetoothManager') # remove

    # gatt server
    GattService=autoclass('android.bluetooth.BluetoothGattService')
    GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')
    GattDescriptor=autoclass('android.bluetooth.BluetoothGattDescriptor')
    GattCallback=autoclass('com.remotemouse.GattCallback') # need a gatt server callback object & BluetoothGattServerCallback is an abstract class
    BluetoothGattServer=autoclass('android.bluetooth.BluetoothGattServer') # remove
    BluetoothGattServerCallback=autoclass('android.bluetooth.BluetoothGattServerCallback') # remove
    BluetoothDevice=autoclass('android.bluetooth.BluetoothDevice')

    # advertising
    AdCallback=autoclass('com.remotemouse.AdCallback') # need an advertise callback object & AdvertiseCallback is an abstract class
    AdvertiseSettings=autoclass('android.bluetooth.le.AdvertiseSettings')
    AdvertiseSettingsBuilder=autoclass('android.bluetooth.le.AdvertiseSettings$Builder')
    AdvertiseData=autoclass('android.bluetooth.le.AdvertiseData')
    AdvertiseDataBuilder=autoclass('android.bluetooth.le.AdvertiseData$Builder')
    AdvertiseCallback=autoclass('android.bluetooth.le.AdvertiseCallback') # remove
    BluetoothLeAdvertiser=autoclass('android.bluetooth.le.BluetoothLeAdvertiser') # remove
except: # this is so I can run it on my laptop to test non-bluetooth stuff
    pass
UUID=autoclass('java.util.UUID')
# bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
def uuid(id):
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

class RemoteMouseApp(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.message="0\n\n"
        self.gatt_callback=None
        self.ad_callback=None
        try: # creating service and characteristics for input data stream
            self.service=GattService(uuid(4500),GattService.SERVICE_TYPE_PRIMARY)
            self.update_message(1,"made service")
            self.characteristics=[]
            for i in range(4):
                self.characteristics.append(GattCharacteristic(uuid(i+4501),
                    GattCharacteristic.PROPERTY_NOTIFY| # for characteristic to support BLE notifications
                    GattCharacteristic.PROPERTY_READ, # allow client to read characteristic's value
                    GattCharacteristic.PERMISSION_READ)) # allow client to read characteristic's value
                self.characteristics[i].setValue(pack("b",0)) # initial value
                descriptor=GattDescriptor(uuid(2902),GattDescriptor.PERMISSION_READ|GattDescriptor.PERMISSION_WRITE) # the client writes to this descriptor to request notifications - unsure if I need read
                descriptor.setValue(GattDescriptor.ENABLE_NOTIFICATION_VALUE) # do I need this as well?
                self.characteristics[i].addDescriptor(descriptor) # add descriptor to characteristic
                print("HERE2",self.characteristics[i].getUuid().toString())
                self.update_message(1,f"made characteristic {i+1}")
                self.service.addCharacteristic(self.characteristics[i])
                self.update_message(1,f"added characteristic {i+1}")
        except Exception as error: # not on the laptop
            self.update_message(2,error)
    
    # updates formatted status/error message which we need stored as I can't see the console on my phone
    def update_message(self,part,new):
        contents=self.message.split("\n")
        contents[part]=str(new)
        self.message=f"{contents[0]}\n{contents[1]}\n{contents[2]}"
        print("HERE1",new)

    def update(self): # called by UI MainWidget to get bluetooth status/errors to display
        if self.message[0]=="0":
            self.update_message(0,"1")
        elif self.message[0]=="1":
            self.update_message(0,"0")
        if self.gatt_callback:
            self.update_message(2,self.gatt_callback.message)
        return self.message

    def setup_ble_server(self):
        try:
            # Getting Bluetooth adapter to check bluetooth is enabled
            self.adapter=BluetoothAdapter.getDefaultAdapter()
            if not self.adapter.isEnabled():
                return False
            self.update_message(1,"bluetooth enabled")
            self.adapter.setName("remote_mouse")
            self.update_message(1,"set name")

            # Setup BLE GATT Server & add previously defined service
            app_context=PythonActivity.mActivity
            bluetooth_manager=app_context.getSystemService(Context.BLUETOOTH_SERVICE) # object to start the server
            self.gatt_callback=GattCallback() # need gatt server callback object to update message
            self.gatt_server=bluetooth_manager.openGattServer(app_context,self.gatt_callback) # server
            self.gatt_callback.addServer(self.gatt_server) # the callback needs the server to respond to read requests
            self.update_message(1,"passed manager/server")
            self.gatt_server.addService(self.service)
            self.update_message(1,"added service")
            return True
        
        except Exception as error:
            self.update_message(2,error)
    
    def advertise(self): # BLE equivalent of becoming discoverable
        try:
            bluetooth_advertiser=self.adapter.getBluetoothLeAdvertiser()
            self.update_message(1,"made advertiser")

            settings_builder=AdvertiseSettingsBuilder()
            # options: ADVERTISE_MODE_LOW_LATENCY, ADVERTISE_MODE_BALANCED, ADVERTISE_MODE_BALANCED
            settings_builder.setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            # options: ADVERTISE_TX_POWER_HIGH, ADVERTISE_TX_POWER_MEDIUM, ADVERTISE_TX_POWER_LOW, ADVERTISE_TX_POWER_ULTRA_LOW
            settings_builder.setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            settings_builder.setConnectable(True)
            settings=settings_builder.build()
            self.update_message(1,"built advertise settings object")
            
            data_builder=AdvertiseDataBuilder()
            data_builder.setIncludeDeviceName(True)
            data=data_builder.build()
            self.update_message(1,"built advertise data object")

            self.ad_callback=AdCallback()
            bluetooth_advertiser.startAdvertising(settings, data, self.ad_callback)
            self.update_message(1,"advertising")

        except Exception as error:
            self.update_message(2,error)
    
    def blueteeth(self): # can probs stick this all in ble setup
        try:
            # may not need
            request_permissions([Permission.BLUETOOTH, Permission.BLUETOOTH_ADMIN, Permission.ACCESS_FINE_LOCATION])
        except: # this is so I can run it on my laptop to test non-bluetooth stuff
            pass

        result=self.setup_ble_server()
        if result:
            self.update_message(1,"server up")
            self.advertise()
        elif result==False:
            self.update_message(1,"bluetooth disabled")

    def build(self):
        return MainWidget()

# UI - currently just outputs touch pos onto the screen
class MainWidget(Widget):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.app=App.get_running_app()
        self.zone=Scatter(do_translation=False,do_rotation=False,do_scale=False) # to detect touches
        self.zone.bind(on_touch_down=self.read_mouse,on_touch_move=self.read_mouse) # when screen touched
        self.out=Label() # to display touch pos
        self.out2=Label(size_hint=(0.9,None)) # to display logs
        self.add_widget(self.zone)
        self.add_widget(self.out)
        self.add_widget(self.out2)
        Clock.schedule_interval(self.update,0.5) # for regular updates
        self.app.blueteeth() # begin bluetooth process - why is this here?
    
    def read_mouse(self,caller,touch): # get touch_pos
        pos=(round(touch.pos[0]),touch.pos[1])
        self.out.text=str(pos)
        self.out.pos=(self.width/2,self.height/2)
        try: # not on the laptop
            self.app.characteristics[0].setValue(pack("d",pos[1])) # package double into byte array
            device=self.app.gatt_callback.device
            if device:
                print("HERE3")
                self.app.gatt_server.notifyCharacteristicChanged(device,self.app.characteristics[0],False)
        except Exception as error:
            self.app.update_message(2,error)
    
    def update(self,dt): # get bluetooth status/errors
        self.out2.text=self.app.update()
        self.out2.pos=(self.width/2,self.height/4)

RemoteMouseApp().run()
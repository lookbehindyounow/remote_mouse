from jnius import autoclass, PythonJavaClass, JavaClass, MetaJavaClass, java_method # remove all bar autoclass
from android.permissions import request_permissions, Permission # this is not a real python library, it's handled at compile-time
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.clock import Clock

# need java classes to do android stuff
try:
    Context=autoclass('android.content.Context')
    PythonActivity=autoclass('org.kivy.android.PythonActivity')

    # bluetooth
    BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothManager=autoclass('android.bluetooth.BluetoothManager') # remove

    # gatt server
    GattCallback=autoclass('com.remotemouse.GattCallback') # need a gatt server callback object & BluetoothGattServerCallback is an abstract class
    BluetoothGattServer=autoclass('android.bluetooth.BluetoothGattServer') # remove
    BluetoothGattServerCallback=autoclass('android.bluetooth.BluetoothGattServerCallback') # remove
    GattService=autoclass('android.bluetooth.BluetoothGattService')
    GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')

    # advertising - test code from chatgpt
    AdCallback=autoclass('com.remotemouse.AdCallback') # need an advertise callback object & AdvertiseCallback is an abstract class
    AdvertiseSettings = autoclass('android.bluetooth.le.AdvertiseSettings')
    AdvertiseSettingsBuilder = autoclass('android.bluetooth.le.AdvertiseSettings$Builder')
    AdvertiseData = autoclass('android.bluetooth.le.AdvertiseData')
    AdvertiseDataBuilder = autoclass('android.bluetooth.le.AdvertiseData$Builder')
    AdvertiseCallback = autoclass('android.bluetooth.le.AdvertiseCallback') # remove
    BluetoothLeAdvertiser = autoclass('android.bluetooth.le.BluetoothLeAdvertiser') # remove
except: # this is so I can run it on my laptop to test non-bluetooth stuff
    pass
UUID=autoclass('java.util.UUID')
# bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
def uuid(id):
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

### - remove below - ###

# this subclass is required because BluetoothGattServerCallback is an abstract class
# & openGattServer (line 75) requires a BluetoothGattServerCallback object
# it doesn't work because "android/bluetooth/BluetoothGattServerCallback is not an interface"
# & without __javainterfaces__ I get "MyBluetoothGattServerCallback has no attribute __javainterfaces__"
# chatgpt gets stuck going back & forth like it's a catch 22
# print("HERE0")
# try:
#     print("HERE1a")
#     class Callback(JavaClass):
#         __javaclass__='com.remotemouse.Callback'
#         __javacontext__='app'
#         def onConnectionStateChange(self, device, status, newState):
#             details=self._call_java_method("onConnectionStateChange")
#             App.get_running_app().update_message(2,details)
#         # @java_method('(Landroid/bluetooth/BluetoothDevice;ILandroid/bluetooth/BluetoothGattCharacteristic;)V')
#         # def onCharacteristicReadRequest(self, device, requestId, offset, characteristic):
#         #     pass
#         # @java_method('(Landroid/bluetooth/BluetoothDevice;ILandroid/bluetooth/BluetoothGattCharacteristic;ZZ[B)V')
#         # def onCharacteristicWriteRequest(self, device, requestId, characteristic, preparedWrite, responseNeeded, offset, value):
#         #     pass
# except: # this is so I can run it on my laptop to test non-bluetooth stuff
#     print("HERE1b")
#     pass
# print("HERE2")

### - remove above - ###

class RemoteMouseApp(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.message="0\n\n"
        self.gatt_callback=None
        self.ad_callback=None
    
    # updates formatted status/error message which we need stored as I can't see the console on my phone
    def update_message(self,part,new):
        contents=self.message.split("\n")
        contents[part]=str(new)
        self.message=f"{contents[0]}\n{contents[1]}\n{contents[2]}"
        print("HERE1",new)

    def update(self): # called by MainWidget to get bluetooth status/errors
        if self.message[0]=="0":
            self.update_message(0,"1")
        elif self.message[0]=="1":
            self.update_message(0,"0")
        if self.ad_callback:
            self.update_message(2,self.ad_callback.message)
        elif self.gatt_callback:
            self.update_message(2,self.gatt_callback.message)
        return self.message

    def setup_ble_server(self):
        try:
            # Getting Bluetooth adapter to check bluetooth is enabled
            if not BluetoothAdapter.getDefaultAdapter().isEnabled():
                return False
            self.update_message(1,"bluetooth enabled")
            # Setup BLE GATT Server
            app_context=PythonActivity.mActivity
            bluetooth_manager=app_context.getSystemService(Context.BLUETOOTH_SERVICE) # object to start the server
            self.gatt_callback=GattCallback() # need gatt server callback object to update message
            self.gatt_server=bluetooth_manager.openGattServer(app_context,self.gatt_callback) # server
            self.update_message(1,"passed manager/server")

            # Input data stream service and characteristics
            service=GattService(uuid("4500"),GattService.SERVICE_TYPE_PRIMARY)
            self.update_message(1,"made service")
            characteristics=[]
            for i in range(4):
                characteristics.append(GattCharacteristic(uuid(f"450{i+1}"),
                    GattCharacteristic.PROPERTY_NOTIFY, # for characteristic to support BLE notifications
                    GattCharacteristic.PERMISSION_READ)) # allow client to read characteristic's value
                self.update_message(1,f"made characteristic {i+1}")
                service.addCharacteristic(characteristics[i])
                self.update_message(1,f"added characteristic {i+1}")
            self.gatt_server.addService(service)
            self.update_message(1,"added service")
            return True
        except Exception as error:
            self.update_message(2,error)
    
    def advertise(self): # chatgpt code
        try:
            bluetooth_advertiser = BluetoothAdapter.getDefaultAdapter().getBluetoothLeAdvertiser()
            self.update_message(1,"made advertiser")
            settings_builder = AdvertiseSettingsBuilder()
            # options: ADVERTISE_MODE_LOW_LATENCY, ADVERTISE_MODE_BALANCED, ADVERTISE_MODE_BALANCED
            settings_builder.setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            # options: ADVERTISE_TX_POWER_HIGH, ADVERTISE_TX_POWER_MEDIUM, ADVERTISE_TX_POWER_LOW, ADVERTISE_TX_POWER_ULTRA_LOW
            settings_builder.setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            settings_builder.setConnectable(True)
            settings=settings_builder.build()
            self.update_message(1,"built settings")
            BluetoothAdapter.getDefaultAdapter().setName("remote_mouse")
            self.update_message(1,"set name")
            data_builder = AdvertiseDataBuilder()
            data_builder.setIncludeDeviceName(True)
            data=data_builder.build()
            self.update_message(1,"built data")
            self.ad_callback = AdCallback()
            bluetooth_advertiser.startAdvertising(settings, data, self.ad_callback)
        except Exception as error:
            self.update_message(2,error)

    def build(self):

        # may not need
        request_permissions([Permission.BLUETOOTH, Permission.BLUETOOTH_ADMIN, Permission.ACCESS_FINE_LOCATION])

        result=self.setup_ble_server()
        if result:
            self.update_message(1,"server up")
            self.advertise()
        elif result==False:
            self.update_message(1,"bluetooth disabled")
        return MainWidget()

# UI - currently just outputs touch pos onto the screen
class MainWidget(Widget):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.zone=Scatter(do_translation=False,do_rotation=False,do_scale=False)
        self.zone.bind(on_touch_down=self.read_mouse,on_touch_move=self.read_mouse) # when screen touched
        self.out=Label()
        self.out2=Label(size_hint=(0.9,None))
        self.add_widget(self.zone)
        self.add_widget(self.out)
        self.add_widget(self.out2)
        Clock.schedule_interval(self.update,0.5)
    
    def read_mouse(self,caller,touch): # get touch_pos
        pos=(round(touch.pos[0]),round(touch.pos[1]))
        self.out.text=str(pos)
        self.out.pos=(self.width/2,self.height/2)
    
    def update(self,dt): # get bluetooth status/errors
        self.out2.text=App.get_running_app().update()
        self.out2.pos=(self.width/2,self.height/4)

RemoteMouseApp().run()
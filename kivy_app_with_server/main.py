from jnius import autoclass, PythonJavaClass, java_method
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.clock import Clock

# need java classes to do android stuff
try:
    Context=autoclass('android.content.Context')
    PythonActivity=autoclass('org.kivy.android.PythonActivity')
    BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothManager=autoclass('android.bluetooth.BluetoothManager')
    BluetoothGattServer=autoclass('android.bluetooth.BluetoothGattServer')
    BluetoothGattServerCallback=autoclass('android.bluetooth.BluetoothGattServerCallback')
    GattService=autoclass('android.bluetooth.BluetoothGattService')
    GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')
except: # this is so I can run it on my laptop to test non-bluetooth stuff
    pass
UUID=autoclass('java.util.UUID')
# bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
def uuid(id):
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

# this subclass is all chatgtp code & is required because
# passing a BluetoothGattServerCallback object straight to openGattServer crashes the program despite the error handler
# but it also doesn't work as "android/bluetooth/BluetoothGattServerCallback is not an interface"
# & without __javainterfaces__ I get "MyBluetoothGattServerCallback has no attribute __javainterfaces__"
# chatgpt is stuck in a loop saying to remove __javainterfaces__
# despite me stating clearly that openGattServer seems to require it, so I'm unsure what to put there
try:
    class MyBluetoothGattServerCallback(PythonJavaClass):
        __javaclass__ = 'android/bluetooth/BluetoothGattServerCallback'
        __javainterfaces__ = ['android/bluetooth/BluetoothGattServerCallback']
        __javacontext__ = 'app'
        @java_method('(Landroid/bluetooth/BluetoothDevice;IIZ)V')
        def onConnectionStateChange(self, device, status, newState):
            App.get_running_app().update_message(2, f"device: {device}, status: {status}, new state: {newState}")
        @java_method('(Landroid/bluetooth/BluetoothDevice;ILandroid/bluetooth/BluetoothGattCharacteristic;)V')
        def onCharacteristicReadRequest(self, device, requestId, offset, characteristic):
            pass
        @java_method('(Landroid/bluetooth/BluetoothDevice;ILandroid/bluetooth/BluetoothGattCharacteristic;ZZ[B)V')
        def onCharacteristicWriteRequest(self, device, requestId, characteristic, preparedWrite, responseNeeded, offset, value):
            pass
except: # this is so I can run it on my laptop to test non-bluetooth stuff
    pass

class RemoteMouseApp(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.message="0\n\n"
    
    # updates formatted status/error message which we need stored as I can't see the console on my phone
    def update_message(self,part,new):
        contents=self.message.split("\n")
        contents[part]=new
        self.message=f"{contents[0]}\n{contents[1]}\n{contents[2]}"

    def update(self): # called by MainWidget to get bluetooth status/errors
        if self.message[0]=="0":
            self.update_message(0,"1")
        elif self.message[0]=="1":
            self.update_message(0,"0")
        return self.message

    def setup_ble_server(self):
        try:
            # Getting Bluetooth adapter to check bluetooth is enabled
            if not BluetoothAdapter.getDefaultAdapter().isEnabled():
                return False
            self.update_message(1,"bluetooth enabled")
            # Setup BLE GATT Server
            app_context=PythonActivity.mActivity
            bt_manager=app_context.getSystemService(Context.BLUETOOTH_SERVICE)
            gatt_server=bt_manager.openGattServer(app_context,MyBluetoothGattServerCallback())
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
            gatt_server.addService(service)
            self.update_message(1,"added service")
            return True
        except Exception as error:
            self.update_message(2,error)

    def build(self):
        result=self.setup_ble_server()
        if result:
            self.update_message(1,"server up")
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
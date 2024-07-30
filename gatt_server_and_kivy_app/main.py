from jnius import autoclass
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.clock import Clock

# need java classes to do android stuff
PythonActivity=autoclass('org.kivy.android.PythonActivity')
BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
BluetoothManager=autoclass('android.bluetooth.BluetoothManager')
BluetoothGattServer=autoclass('android.bluetooth.BluetoothGattServer')
GattService=autoclass('android.bluetooth.BluetoothGattService')
GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')
UUID=autoclass('java.util.UUID')
# bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
def uuid(id):
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

class RemoteMouseApp(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.message="dating;server down;"
    
    def update_message(self,part,new):
        contents=self.message.split(";")
        contents[part]=new
        self.message=f"{contents[0]};{contents[1]};{contents[2]}"

    def update(self):
        if self.message[0]=="u":
            self.update_message(self,0,"dating")
        elif self.message[0]=="d":
            self.update_message(self,0,"up")
        return self.message

    def setup_ble_server(self):
        # Getting Bluetooth adapter to check bluetooth is enabled
        if not BluetoothAdapter.getDefaultAdapter().isEnabled():
            return False
        self.update_message(self,2,"bluetooth enabled")
        # Setup BLE GATT Server
        bt_manager=PythonActivity.mActivity.getSystemService(self.get_context(),BluetoothManager.BLUETOOTH_SERVICE)
        gatt_server=bt_manager.openGattServer(self.get_context(),self.gatt_server_callback)
        self.update_message(self,2,"passed manager/server")

        # Input data stream service and characteristics
        service=GattService(uuid("4500"),GattService.SERVICE_TYPE_PRIMARY)
        self.update_message(self,2,"made service")
        characteristics=[]
        for i in range(4):
            characteristics.append(GattCharacteristic(uuid(f"450{i+1}"),
                GattCharacteristic.PROPERTY_NOTIFY, # for characteristic to support BLE notifications
                GattCharacteristic.PERMISSION_READ)) # allow client to read characteristic's value
            self.update_message(self,2,f"made characteristic {i+1}")
            service.addCharacteristic(characteristics[i])
            self.update_message(self,2,f"added characteristic {i+1}")
        gatt_server.addService(service)
        self.update_message(self,2,"added service")
        return True

    def gatt_server_callback(self,device,status,newState):
        self.update_message(self,2,f"device: {device}, status: {status}, new state: {newState}")

    def build(self):
        if self.setup_ble_server():
            self.update_message(self,1,"server up")
        else:
            self.update_message(self,1,"bluetooth disabled")
        return MainWidget()

# UI - currently just outputs touch pos onto the screen
class MainWidget(Widget):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.zone=Scatter(do_translation=False,do_rotation=False,do_scale=False)
        self.zone.bind(on_touch_down=self.read_mouse,on_touch_move=self.read_mouse)
        self.out=Label()
        self.out2=Label()
        self.add_widget(self.zone)
        self.add_widget(self.out)
        self.add_widget(self.out2)
        Clock.schedule_interval(self.update,0.5)
    
    def read_mouse(self,caller,touch):
        self.out.text=str(touch.pos)
        self.out.pos=(self.width/2,self.height/2)
    
    def update(self,dt):
        self.out2.text=App.get_running_app().update()
        self.out2.pos=(self.width/2,self.height/4)

RemoteMouseApp().run()
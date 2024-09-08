from jnius import autoclass
from struct import pack
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
Context=autoclass('android.content.Context')
PythonActivity=autoclass('org.kivy.android.PythonActivity')
BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice=autoclass('android.bluetooth.BluetoothDevice')
GattService=autoclass('android.bluetooth.BluetoothGattService')
GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')
GattDescriptor=autoclass('android.bluetooth.BluetoothGattDescriptor')
GattCallback=autoclass('com.remotemouse.GattCallback')
AdvertiseSettings=autoclass('android.bluetooth.le.AdvertiseSettings')
AdvertiseSettingsBuilder=autoclass('android.bluetooth.le.AdvertiseSettings$Builder')
AdvertiseData=autoclass('android.bluetooth.le.AdvertiseData')
AdvertiseDataBuilder=autoclass('android.bluetooth.le.AdvertiseData$Builder')
ParcelUUID=autoclass("android.os.ParcelUuid")
AdCallback=autoclass('com.remotemouse.AdCallback')
UUID=autoclass('java.util.UUID')
def uuid(id):
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

class Test(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.service=GattService(uuid(4500),GattService.SERVICE_TYPE_PRIMARY)
        self.characteristic=GattCharacteristic(uuid(4500),
            GattCharacteristic.PROPERTY_NOTIFY|
            GattCharacteristic.PROPERTY_READ,
            GattCharacteristic.PERMISSION_READ|
            GattCharacteristic.PERMISSION_WRITE)
        self.characteristic.setValue(pack("H",0))
        descriptor=GattDescriptor(uuid(2902),GattDescriptor.PERMISSION_WRITE)
        self.characteristic.addDescriptor(descriptor)
        self.service.addCharacteristic(self.characteristic)

        self.adapter=BluetoothAdapter.getDefaultAdapter()
        self.adapter.setName("remote_mouse")
        app_context=PythonActivity.mActivity
        bluetooth_manager=app_context.getSystemService(Context.BLUETOOTH_SERVICE)
        self.gatt_callback=GattCallback()
        self.gatt_server=bluetooth_manager.openGattServer(app_context,self.gatt_callback)
        self.gatt_callback.setServer(self.gatt_server)
        self.gatt_server.addService(self.service)

        bluetooth_advertiser=self.adapter.getBluetoothLeAdvertiser()
        settings_builder=AdvertiseSettingsBuilder()
        settings_builder.setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
        settings_builder.setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
        settings_builder.setConnectable(True)
        settings=settings_builder.build()
        data_builder=AdvertiseDataBuilder()
        data_builder.setIncludeDeviceName(True).addServiceUuid(ParcelUUID(uuid(4500)))
        data=data_builder.build()
        self.ad_callback=AdCallback()
        bluetooth_advertiser.startAdvertising(settings,data,self.ad_callback)

    def build(self):
        return MainWidget(self)

class MainWidget(BoxLayout):
    def __init__(self,app,**kwargs):
        super().__init__(**kwargs)
        self.app=app
        self.bind(on_touch_down=self.send)
        self.screen_logs=Label()
        self.add_widget(self.screen_logs)
    
    def send(self,*args):
        self.app.characteristic.setValue(pack("H",0))
        device=self.app.gatt_callback.device
        if device:
            self.app.gatt_server.notifyCharacteristicChanged(device,self.app.characteristic,False)

Test().run()
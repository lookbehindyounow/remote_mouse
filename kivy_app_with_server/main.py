from jnius import autoclass, PythonJavaClass, java_method # this allows us to work with java classes so we can use android bluetooth api
from struct import pack # to turn variables into byte arrays
from math import floor, ceil # for button pos calc
from time import time # for notification frequency logging

# for UI
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import InstructionGroup, Rectangle, Triangle, Ellipse, Line, Translate, Rotate, Scale
from kivy.metrics import dp
from kivy.clock import Clock

# need java classes to do android stuff
try: # but these would all throw errors when testing UI on the laptop so I've put them in a try block
    # java context stuff
    Context=autoclass('android.content.Context')
    PythonActivity=autoclass('org.kivy.android.PythonActivity')

    # bluetooth
    BluetoothAdapter=autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothDevice=autoclass('android.bluetooth.BluetoothDevice')

    # gatt server
    GattService=autoclass('android.bluetooth.BluetoothGattService')
    GattCharacteristic=autoclass('android.bluetooth.BluetoothGattCharacteristic')
    GattDescriptor=autoclass('android.bluetooth.BluetoothGattDescriptor')
    GattCallback=autoclass('com.remotemouse.GattCallback') # custom gatt server callback class

    # advertising
    AdvertiseSettings=autoclass('android.bluetooth.le.AdvertiseSettings')
    AdvertiseSettingsBuilder=autoclass('android.bluetooth.le.AdvertiseSettings$Builder')
    AdvertiseData=autoclass('android.bluetooth.le.AdvertiseData')
    AdvertiseDataBuilder=autoclass('android.bluetooth.le.AdvertiseData$Builder')
    ParcelUUID=autoclass("android.os.ParcelUuid") # UUIDs need to be parcel UUIDs for advertising
    AdCallback=autoclass('com.remotemouse.AdCallback') # custom advertise server callback class
except:
    pass

UUID=autoclass('java.util.UUID') # data type
def uuid(id): # bluetooth SIG standard format for UUIDs: 0000xxxx-0000-1000-8000-00805f9b34fb
    return UUID.fromString(f"0000{id}-0000-1000-8000-00805f9b34fb")

class JavaMessenger(PythonJavaClass): # implementation of a class that calls a python method from java object
    __javainterfaces__=["com/remotemouse/IJavaMessenger"] # custom interface
    __javacontext__="app" # for class loader to be able to see custom interface
    def __init__(self,app):
        self.app=app
    @java_method("(Ljava/lang/String;)V")
    def callInPython(self,message):
        self.app.update_message(1,message)

class RemoteMouseApp(App): # app
    def update_message(self,part,new): # method to update log/status thing displayed on screen for debug
        # 3 lines, top is binary data to send as 2-byte characteristic, middle is just general logs & bottom is errors
        contents=self.message.split("\n")
        contents[part]=new
        self.message=f"{contents[0]}\n{contents[1]}\n{contents[2]}"
        print(f"HERE{part}",new) # log message update in console
        try:
            self.ui.screen_logs.text=self.message
        except AttributeError: # if screen_logs doesn't exist yet do nothing
            pass

    def __init__(self,**kwargs):
        self.start_time=time()
        super().__init__(**kwargs) # init kivy app stuff
        self.message="\n\n" # contents of a 3 line log/status label displayed on screen for debug

        try: # creating service and characteristics for input data stream, android only hence try block
            self.service=GattService(uuid(4500),GattService.SERVICE_TYPE_PRIMARY) # service
            self.update_message(1,"made service")

            self.characteristic=GattCharacteristic(uuid(4500), # characteristic
                GattCharacteristic.PROPERTY_NOTIFY| # for characteristic to support BLE notifications
                GattCharacteristic.PROPERTY_READ, # not required for client to receive notifcations
                GattCharacteristic.PERMISSION_READ| # not required for client to receive notifcations
                GattCharacteristic.PERMISSION_WRITE) # for experimenting with Client.stay_awake(), so far hasn't fixed issue
            self.update_message(1,f"made characteristic with UUID: {uuid(4500)}")

            self.characteristic.setValue(pack("H",0)) # initial value, pack into bye array
            self.update_message(1,"set characteristic initial value")

            descriptor=GattDescriptor(uuid(2902),GattDescriptor.PERMISSION_WRITE) # Client Characteristic Configuration Descriptor
            # the client writes to this^ descriptor to request notifications & it has to have that specific UUID
            self.update_message(1,"made CCCD")
            self.characteristic.addDescriptor(descriptor) # add descriptor to characteristic
            self.update_message(1,"added CCCD to characteristic")

            self.service.addCharacteristic(self.characteristic)
            self.update_message(1,"added characteristic to service")

        except Exception as error:
            self.update_message(2,error)

        self.setup() # begin bluetooth process

    def setup(self):
        try:
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

            self.java_messenger=JavaMessenger(self) # java object to update screen_logs from GattCallback.onConnectionStateChange
            self.gatt_callback=GattCallback(self.java_messenger) # callback object for gatt server
            self.gatt_server=bluetooth_manager.openGattServer(app_context,self.gatt_callback) # create gatt server
            self.gatt_callback.setServer(self.gatt_server) # not required for client to receive notifcations
            self.update_message(1,"created server")

            self.gatt_server.addService(self.service) # add previously defined service with characteristics to server
            self.update_message(1,"added service to server")

            self.advertise() # make discoverable

        except Exception as error:
            self.update_message(2,error)
    
    def advertise(self): # make discoverable
        try:
            bluetooth_advertiser=self.adapter.getBluetoothLeAdvertiser() # getting android's BLE advertiser
            self.update_message(1,"got BLE advertiser")

            settings_builder=AdvertiseSettingsBuilder()
            # options: ADVERTISE_MODE_LOW_LATENCY, ADVERTISE_MODE_BALANCED, ADVERTISE_MODE_BALANCED
            settings_builder.setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            # options: ADVERTISE_TX_POWER_HIGH, ADVERTISE_TX_POWER_MEDIUM, ADVERTISE_TX_POWER_LOW, ADVERTISE_TX_POWER_ULTRA_LOW
            settings_builder.setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            settings_builder.setConnectable(True)
            settings=settings_builder.build() # settings object for advertiser
            self.update_message(1,"built advertise settings object")

            data_builder=AdvertiseDataBuilder()
            data_builder.setIncludeDeviceName(True).addServiceUuid(ParcelUUID(uuid(4500))) # UUIDs need to be parcel UUIDs for advertising
            data=data_builder.build() # data object for advertiser
            self.update_message(1,"built advertise data object")

            self.ad_callback=AdCallback(self.java_messenger) # callback object for advertiser, also uses JavaMessenger for python logging
            bluetooth_advertiser.startAdvertising(settings,data,self.ad_callback)
            self.update_message(1,"starting advertiser...")

        except Exception as error:
            self.update_message(2,error)

    def build(self):
        self.ui=MainWidget(self)
        return self.ui # give kivy the UI

class MainWidget(BoxLayout): # UI
    def __init__(self,app,**kwargs):
        super().__init__(**kwargs)
        self.input_buffer=0 # this is where the current input will be written to before it's packaged into 2 bytes & sent
        self.app=app # get app
        self.padding=dp(20)
        self.spacing=dp(10)

        self.button_container=GridLayout()
        self.add_widget(self.button_container)
        self.isShifted=False
        self.button_names=[["up arrow","right arrow","left arrow","down arrow","left mouse","shift"], # button text
                            ["<unassigned>","volume up","<unassigned>","volume down","right mouse","shift"]] # shifted button text
        self.buttons=[Button() for i in range(6)]
        i=0
        for button in self.buttons: # create buttons
            button.i=i # for easy identification
            button.font_size=dp(30) # can remove if/when there's no text on buttons
            button.bind(on_press=self.press,on_release=self.release)
            button.icon=Widget() # for an extra canvas that we can clear without removing the button's own graphic
            button.add_widget(button.icon)
            button.current_icon=None
            if i<4: # arrow button icons
                button.arrow=InstructionGroup()
                button.arrow.add(Rotate(angle=[0,270,90,180,0,0][i],origin=(0,0))) # change canvas rotation for each arrow
                button.arrow.add(Rectangle(pos=(dp(-12),dp(-24)),size=(dp(24),dp(24))))
                button.arrow.add(Triangle(points=(dp(-30),0,0,dp(24),dp(30),0)))
                button.arrow.add(Rotate(angle=[0,90,270,180][i],origin=(0,0)))
            if i==4: # mouse button icons
                button.left_mouse=InstructionGroup()
                button.left_mouse.add(Rectangle(pos=(dp(-25),dp(-10)),size=(dp(50),dp(20))))
                button.left_mouse.add(Ellipse(pos=(dp(-25),dp(-35)),size=(dp(50),dp(50)),angle_start=90,angle_end=270))
                button.left_mouse.add(Ellipse(pos=(dp(-25),dp(-15)),size=(dp(50),dp(50)),angle_end=90))
                button.left_mouse.add(Line(ellipse=(dp(-23.5),dp(-3.5),dp(37),dp(37),-90,0),width=dp(1.5)))
                button.left_mouse.add(Line(points=(dp(-23.5),dp(15),dp(-5),dp(15),dp(-5),dp(33.5)),width=dp(1.5)))
                button.right_mouse=InstructionGroup()
                button.right_mouse.add(Scale(x=-1,y=1,origin=(0,0))) # flip for right mouse icon
                for instruction in button.left_mouse.children: # copy instructions
                    button.right_mouse.add(instruction)
                button.right_mouse.add(Scale(x=-1,y=1,origin=(0,0)))
            if i in [1,3]: # for volume button icons
                button.volume=InstructionGroup()
                button.volume.add(Rectangle(pos=(dp(-19.5),dp(-8)),size=(dp(12),dp(16))))
                button.volume.add(Triangle(points=(dp(-17.5),0,dp(7.5),dp(20),dp(7.5),dp(-20))))
                button.volume.add(Line(ellipse=(dp(-3),dp(-9),dp(18),dp(18),45,135),width=dp(1.5)))
                if i==1: # for volume up button
                    button.volume.add(Line(ellipse=(dp(-6.5),dp(-13.5),dp(27),dp(27),45,135),width=dp(1.5)))
                    button.volume.add(Line(ellipse=(dp(-10),dp(-18),dp(36),dp(36),45,135),width=dp(1.5)))
            if i==5: # shift button icons
                button.circle=Line(circle=(0,0,dp(20)),width=dp(4))
            i+=1
        self.release(self.buttons[5]) # call release shift button to give buttons their normal names & icons to start

        self.mouse_pad=Widget() # to detect touches
        self.mouse_pad.bind(on_touch_down=self.read_mouse,on_touch_move=self.read_mouse) # binding screen touch methods
        self.mouse_pad.bind(on_touch_up=self.reset_mouse)
        self.reset_mouse(None,None) # init x0 & y0 for mouse v calc
        self.add_widget(self.mouse_pad)

        self.screen_logs=Label(valign="center") # to display log/status thing for debug
        self.mouse_pad.add_widget(self.screen_logs)
        Clock.schedule_once(lambda dt: self.app.update_message(1,"screen logs running")) # put text in screen_logs
        # scheduled because app doesn't have ui attribute yet, so update_message won't be able to change screen_logs.text until next frame

    def on_size(self,caller,size):
        if self.width>self.height: # landscape
            self.orientation="horizontal"
            self.button_container.clear_widgets()
            self.button_container.rows=2
            [self.button_container.add_widget(self.buttons[i]) for i in [0,1,5,2,3,4]] # order of buttons is different for landscape
        else: # portrait
            self.orientation="vertical"
            self.button_container.clear_widgets()
            self.button_container.rows=3
            [self.button_container.add_widget(self.buttons[i]) for i in range(6)]
        # when you rotate your phone it calls on_size before widget positions have updated
        Clock.schedule_once(self.place_label_and_icons) # things that need scheduled for next frame cause they depend on values that haven't changed yet
    
    def place_label_and_icons(self,dt):
        self.screen_logs.pos=self.mouse_pad.to_parent(0,0,True) # display log/status thing in mouse_pad
        self.screen_logs.size=self.mouse_pad.size # for valign="center" to work as expected
        self.screen_logs.text_size=self.mouse_pad.size # so all text stays on screen
        for button in self.buttons: # place icons for each button
            if button.current_icon: # that has an icon
                button.icon.canvas.clear()
                button.icon.canvas.add(Translate(button.center_x,button.center_y)) # translate canvas to button pos
                button.icon.canvas.add(button.current_icon) # draw current icon
                button.icon.canvas.add(Translate(-button.center_x,-button.center_y))
    
    def read_mouse(self,caller,touch): # handle mouse pad input
        if self.mouse_pad.collide_point(*touch.pos): # only if touch pos is within mouse pad pos
            x,y=self.mouse_pad.to_local(*touch.pos,True) # get coords relative to mouse pad origin
            if self.x0!=None and self.y0!=None: # don't send first touch
                dx=x-self.x0 # get x & y direction (ints)
                dy=y-self.y0

                self.input_buffer&=63 # keep only last 6 bits - wipe pos data (first 10 bits) to 0s
                if dx<0: self.input_buffer|=32768 # bit 1 is sign bit for dx
                if dy>0: self.input_buffer|=1024 # bit 6 is sign bit for dy (inverted cause mac screen coords start in top left)

                dx=min(ceil(abs(dx/4)),15) # get x & y int direction magnitude scaled down, capped at 15 (to fit into 4 bits each)
                dy=min(ceil(abs(dy/4)),15)
                self.input_buffer|=(dx<<11)|(dy<<6) # put 4 bit representations of dx & dy into places 2-5 & 7-10 respectively

                self.send()
            self.x0,self.y0=x,y # update last position for next frame's direction
    
    def reset_mouse(self,caller,touch): # re-initialise mouse tracking at end of touch
        self.x0,self.y0=None,None
        self.input_buffer&=63 # wipe pos data (first 10 bits) to 0s
    
    def press(self,caller): # handle button press
        self.input_buffer|=(32>>caller.i) # set relevant button bit (positions 11-16) to 1
        self.send()
        if caller.i==5: # if shift button
            for button,name in zip(self.buttons,self.button_names[1]):
                button.icon.canvas.clear()
                button.current_icon=None
                button.text=""
                if button.i in [1,3]: # for volume buttons
                    button.current_icon=button.volume
                elif button.i==4: # for mouse button
                    button.current_icon=button.right_mouse
                elif button.i==5: # for shift button
                    button.current_icon=button.circle
                else:
                    button.text=name # otherwise give button shifted name
                if button.current_icon:
                    button.icon.canvas.add(Translate(button.center_x,button.center_y)) # translate canvas to button pos
                    button.icon.canvas.add(button.current_icon) # draw current icon
                    button.icon.canvas.add(Translate(-button.center_x,-button.center_y))
    
    def release(self,caller): # handle button release
        self.input_buffer&=65535-(32>>caller.i) # set relevant button bit (positions 11-16) to 0
        self.send()
        if caller.i==5: # if shift button
            for button,name in zip(self.buttons,self.button_names[0]):
                button.icon.canvas.clear()
                button.current_icon=None
                button.text=""
                if button.i<4: # for arrow buttons
                    button.current_icon=button.arrow
                elif button.i==4: # for mouse button
                    button.current_icon=button.left_mouse
                else:
                    button.text=name # otherwise give button unshifted name
                if button.current_icon:
                    button.icon.canvas.add(Translate(button.center_x,button.center_y)) # translate canvas to button pos
                    button.icon.canvas.add(button.current_icon) # draw current icon
                    button.icon.canvas.add(Translate(-button.center_x,-button.center_y))
    
    def send(self): # log input, update characteristic & notify client
        self.app.update_message(0,f"{self.input_buffer:016b}")
        try:
            self.app.characteristic.setValue(pack("H",self.input_buffer)) # package double into byte array for new characteristic values
            device=self.app.gatt_callback.device
            if device:
                self.app.gatt_server.notifyCharacteristicChanged(device,self.app.characteristic,False)
        except Exception as error:
            self.app.update_message(2,error)

RemoteMouseApp().run() # initialise & build app
from jnius import autoclass, PythonJavaClass, java_method, JavaClass, MetaJavaClass
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label

class Spy(str):
    pass
    def replace(self,*args):
        print("HERE0")
        return super().replace(*args)
    def encode(self,*args):
        print("HERE1")
        return super().encode(*args)

class Print(PythonJavaClass):
    __javainterfaces__=[Spy("com/example/IPrint")]
    __javacontext__="app"
    @java_method("(Ljava/lang/String;)V")
    def jprint(self,message):
        print(message)

Holder=autoclass("com.example.Holder")
JavaPrint=autoclass("com.example.Print")

class Test(App):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.printer=Print()
        # self.printer=JavaPrint()
        self.holder=Holder(self.printer)
        self.holder.jprint("hi")
    
    def build(self):
        return MainWidget()

class MainWidget(Widget):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="kivy working"))

Test().run()
# printer=Print()
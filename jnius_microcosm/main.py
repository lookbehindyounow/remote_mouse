from jnius import autoclass, PythonJavaClass, java_method, JavaClass, MetaJavaClass
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label

class Print(PythonJavaClass):
    __javainterfaces__=["com/example/IPrint"]

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
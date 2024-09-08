// IMPORTANT RULE WITH NO EXAMPLE IN CODE: it's "self" in objc & "this" in c++
// it's also "import" for objc libraries vs "include" for c++
#import <Foundation/Foundation.h> // this has all the basic the NS stuff
#import <CoreBluetooth/CoreBluetooth.h> // macbook bluetooth api
#include <cstring> // for data processing
#include <ApplicationServices/ApplicationServices.h> // for controlling laptop
#include <cmath> // for mouse movement processing
#include <Carbon/Carbon.h> // for kVK_ANSI key codes
#import <Cocoa/Cocoa.h> // for NSEvent
#include <ctime> // for measuring time
// #include <mach/mach.h> // for logging how much memory is being used
// #include <mach/task_info.h>

// class BLEScanner; // declaring c++ class BLEScanner so it can be referenced in BLEDelegate, commented cause it's not currently being referenced in BLEDelegate

// objc class declaration, inherits from NSObject and CBCentralManagerDelegate & CBPeripheralDelegate protocols (protocol≈interface)
@interface BLEDelegate: NSObject <CBCentralManagerDelegate,CBPeripheralDelegate>
// nonatomic: not thread-safe, doesn't use any locks (faster)
// atomic: thread-safe (small but possible chance of connectionAttemptNumber being accessed by 2 different threads simoultaneously)
// strong: strong reference, adds to reference count & effectively holds on to object so it isn't deallocated until it's no longer being used by holder
// weak: weak reference, doesn't add to reference count so it's not holding onto the object or preventing deallocation
// assign: like a weak reference but also for primitive types?
@property(nonatomic,strong) CBPeripheral* connectedPeripheral; // delagate needs to hold onto peripheral after discovering so it isn't released before it can connect
// @property(nonatomic,weak) BLEScanner* scanner; // for delegate object to contain a reference to the scanner, commented cause it's not necessary yet but may be useful later
@property(atomic,assign) int connectionAttemptNumber; // to ensure the connection timeout doesn't cancel subsequent connection attempts in fast connect/disconnect scenarios
// @property(nonatomic,assign) int timesConnected; // to compare with memory being used to check for memory leaks
@property(nonatomic,assign) int connectionTime; // to measure connectionn duration
@property(nonatomic,assign) uint8_t buttonStates; // will treat as a boolean array with bitwise logic to store current button states
@property(atomic,assign) bool swiping; // shift + horizontal swipe takes a while so this ensures it's only happening once at any given time
@end

@implementation BLEDelegate // objc class defenition/implementation
-(instancetype)init{
    self=[super init];
    self.connectionAttemptNumber=0;
    // self.timesConnected=0;
    self.swiping=false;
    return self;
}

-(void)centralManagerDidUpdateState:(CBCentralManager*)central{ // "-" means instance level ("+" would be class level), argument "central" is a "CBCentralManager" pointer
    if (central.state==CBManagerStatePoweredOn){
        // methods in objc are referenced with their parameters inside the method name
        [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // objc method call: [object namePart1:arg1 namePart2:arg2];
        NSLog(@"Scanning...");
        // [CBUUID UUIDWithString:@"4500"] is target service UUID, should make this more dynamic at some point
    } else{
        NSLog(@"Bluetooth is not available.");
    }
}

// objc method definition: +/-(return type)namePart1:(arg1Type)arg1... namePartN:(argNType)argN {implementation}, argTypes are pointers, primitives or structs
-(void)centralManager:(CBCentralManager*)central didDiscoverPeripheral:(CBPeripheral*)peripheral advertisementData:(NSDictionary<NSString*,id>*)advertisementData RSSI:(NSNumber*)RSSI{
    // NSLog(@"Discovered device: %@, RSSI: %@",peripheral.name,RSSI);
    if ([peripheral.name isEqualToString:@"remote_mouse"]){
        [central stopScan];
        peripheral.delegate=self; // BLEDelegate inherits from CBCentralManagerDelegate & CBPeripheralDelegate protocols so can be used for both
        NSLog(@"Connecting to %@...",peripheral.name);
        [central connectPeripheral:peripheral options:nil];
        self.connectionAttemptNumber++;
        int thisAttempt=self.connectionAttemptNumber;

        // delay timeout without blocking the main thread with dispatch_after(when,queue,function), anonymous functions in objc are notated ^{code}
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(5e9)),dispatch_get_main_queue(),^{
            if (self.connectionAttemptNumber==thisAttempt && peripheral.state==1){ // if this attempt still connecting after timeout
                [central cancelPeripheralConnection:peripheral];
                NSError* error=[NSError errorWithDomain:@"com.remotemouse" code:0 userInfo:@{NSLocalizedDescriptionKey:@"timed out"}];
                [self centralManager:central didFailToConnectPeripheral:peripheral error:error];
            }
        });
        self.connectedPeripheral=peripheral; // for reference counting, if this peripheral isn't held onto it's deallocated after this method returns
    }
}

-(void)centralManager:(CBCentralManager*)central didConnectPeripheral:(CBPeripheral*)peripheral{
    self.connectionTime=time(0);
    self.buttonStates=0;
    NSLog(@"Connected to %@ server",peripheral.name);
    // self.timesConnected++;
    // NSLog(@"times connected: %i",self.timesConnected); // log times connected to compare with current used memory size
    [peripheral discoverServices:nil];
    // [central cancelPeripheralConnection:peripheral]; // disconect upon connection for testing
}

-(void)centralManager:(CBCentralManager*)central didFailToConnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"Failed to connect to %@ server",peripheral.name);
    NSLog(@"Error: %@",error.localizedDescription);
    self.connectedPeripheral=nil; // strong reference set to nil tells compiler to decrement reference count of the CBPeripheral (from 1 to 0, so it will be deallocated)
    NSLog(@"\n");
    NSLog(@"Scanning...");
    [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // restart scan
}

-(void)centralManager:(CBCentralManager*)central didDisconnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"\n");
    NSLog(@"Disconnected from %@ server",peripheral.name);
    error?NSLog(@"Error: %@",error.localizedDescription):
    NSLog(@"Connected for %lis",time(0)-self.connectionTime);
    self.connectedPeripheral=nil; // strong reference set to nil tells compiler to decrement reference count of the CBPeripheral (from 1 to 0, so it will be deallocated)
    NSLog(@"\n");
    NSLog(@"Scanning...");
    [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // restart scan
}

-(void)peripheral:(CBPeripheral*)peripheral didDiscoverServices:(NSError*)error{ // services are in peripheral.services after running discoverServices
    if (error){
        NSLog(@"Error discovering services: %@",error.localizedDescription);
        return;
    }
    NSLog(@"Services:");
    for (CBService* service in peripheral.services){
        NSLog(@"  Service UUID: %@",service.UUID);
        [peripheral discoverCharacteristics:nil forService:service];
    }
}

-(void)peripheral:(CBPeripheral*)peripheral didDiscoverCharacteristicsForService:(CBService*)service error:(NSError*)error{
    if (error){
        NSLog(@"  Error discovering characteristics: %@",error.localizedDescription);
        return;
    }
    NSLog(@"  Characteristics:");
    for (CBCharacteristic* characteristic in service.characteristics){
        NSLog(@"    Characteristic UUID: %@; subscribing",characteristic.UUID);
        // [peripheral readValueForCharacteristic:characteristic];
        [peripheral setNotifyValue:true forCharacteristic:characteristic];
    }
    int thisAttempt=self.connectionAttemptNumber;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(5e9)),dispatch_get_main_queue(),^{ // attempt at a keep alive method
        if (self.connectionAttemptNumber==thisAttempt && peripheral.state==2){ // if this attempt still connected after 10s
            short data=0;
            NSLog(@"0");
            [peripheral writeValue:[NSData dataWithBytes:&data length:2] forCharacteristic:service.characteristics[0] type:CBCharacteristicWriteWithResponse];
            NSLog(@"1");
        }
    });
}

-(void)peripheral:(CBPeripheral*)peripheral didUpdateValueForCharacteristic:(CBCharacteristic*)characteristic error:(NSError*)error{
    if (error){
        NSLog(@"Error receiving notification for characteristic %@: %@",characteristic.UUID,error.localizedDescription);
        return;
    }

    short bytes; // put raw bytes from characteristic.value's property "bytes" into a short (cause it's 2 bytes)
    memcpy(&bytes,[characteristic.value bytes],2);

    // char bits[16];
    // for (short i=0;i<16;i++){
    //     bits[i]=bytes&(32768>>i)?'1':'0'; // for each bit in "bytes", add a 1 or 0 to binary string "bits"
    // }
    // char x[6];char y[6];char buttons[7];
    // strncpy(x,bits,5);strncpy(y,bits+5,5);strncpy(buttons,bits+10,6); // split bits up into sections for x, y & buttons
    // x[5]='\0';y[5]='\0';buttons[6]='\0'; // add null terminators
    // NSLog(@"%s %s %s",x,y,buttons); // display bits with spaces between sections

    CGEventRef event; // declare event
    CGPoint pos=CGEventGetLocation(CGEventCreate(nullptr)); // get mouse pos
    uint8_t dx=(bytes&30720)>>11; // mouse x speed from characteristic
    uint8_t dy=(bytes&960)>>6; // mouse y speed from characteristic
    if (dx||dy && !self.swiping){ // if mouse moves & not already in a shift+sideways swipe
        dx*=(dx+1)/2; // input scaling
        dy*=(dy+1)/2;
        if (!(bytes&1)){ // shift not pressed
            pos.x+=dx*(bytes&32768?-1:1);
            pos.y+=dy*(bytes&1024?-1:1);
            // creates mouse move event, (source,type,pos,button), button is ignored unless type is kCGEventOtherMouseSomething
            event=CGEventCreateMouseEvent(nullptr,kCGEventMouseMoved,pos,(CGMouseButton)0);
        } else if (dx>=2*dy){ // shift pressed & sideways swipe
            self.swiping=true;
            CGKeyCode key=bytes&32768?kVK_RightArrow:kVK_LeftArrow;
            event=CGEventCreateKeyboardEvent(nullptr,kVK_Control,true); // control down
            CGEventPost(kCGHIDEventTap,event);
            CFRelease(event);
            usleep(500); // delays because macbook gets confused when these are executed too fast & the key combos don't work
            event=CGEventCreateKeyboardEvent(nullptr,key,true); // arrow key down
            CGEventPost(kCGHIDEventTap,event);
            CFRelease(event);
            usleep(500);
            event=CGEventCreateKeyboardEvent(nullptr,key,false); // arrow key up
            CGEventPost(kCGHIDEventTap,event);
            CFRelease(event);
            usleep(500);
            event=CGEventCreateKeyboardEvent(nullptr,kVK_Control,false); // control up
            self.swiping=false;
        } else{ // shift pressed & upward swipe
            event=CGEventCreateScrollWheelEvent(nullptr,kCGScrollEventUnitPixel,1,bytes&1024?-dy:dy);
        }
        CGEventPost(kCGHIDEventTap,event);
        CFRelease(event); // release event for memory management
    }

    for (uint8_t i=0;i<6;i++){ // loop through app buttons
        bool isPressed;
        if (bytes&(32>>i) && !(self.buttonStates&(32>>i))){ // if app button pressed & button state 0
            self.buttonStates|=(32>>i); // change button state to 1
            isPressed=true;
        } else if (!(bytes&(32>>i)) && self.buttonStates&(32>>i)){ // if app button not pressed & button state 1
            self.buttonStates&=255-(32>>i); // change button state to 0
            isPressed=false;
        } else{ // if no change in button state, skip event creation & posting, continue to next button
            continue;
        }

        CGEventType mouseButton;
        CGKeyCode key;
        int data;
        switch (i){ // choose event params by button index
            case 0: // up arrow / unassigned button
                // !(self.buttonStates&1)?
                if (!(self.buttonStates&1)){
                    key=kVK_UpArrow;
                } else{
                    continue; // unassigned, skip
                }
                break;
            case 1: // right arrow / volume up button
                !(self.buttonStates&1)?
                key=kVK_RightArrow:
                data=0;
                break;
            case 2: // left arrow / unassigned button
                // !(self.buttonStates&1)?
                if (!(self.buttonStates&1)){
                    key=kVK_LeftArrow;
                } else{
                    continue; // unassigned, skip
                }
                break;
            case 3: // down arrow / volume down button
                !(self.buttonStates&1)?
                key=kVK_DownArrow:
                data=65536;
                break;
            case 4: // mouse button
                !(self.buttonStates&1)? // not (shift pressed)?
                mouseButton=isPressed?kCGEventLeftMouseDown:kCGEventLeftMouseUp: // left mouse
                mouseButton=isPressed?kCGEventRightMouseDown:kCGEventRightMouseUp; // right mouse
                break;
            case 5: // shift button
                continue; // all it does is update buttonStates&16 which has already happened so skip
        }

        if (self.buttonStates&1&&(i==1||i==3)){ // if volume button
            short intPressed;
            intPressed=isPressed?0xa00:0xb00;
            NSEvent* cocoaEvent=[NSEvent otherEventWithType:NSEventTypeSystemDefined location:NSZeroPoint // create NSEvent
                modifierFlags:intPressed // variable input
                timestamp:0 windowNumber:0 context:nil subtype:8 // don't know what these do
                data1:data|intPressed // variable input
                data2:-1]; // don't know what these do
            event=[cocoaEvent CGEvent]; // get CGEvent from NSEvent
            CGEventPost(kCGHIDEventTap,event); // post event, we can't release it cause it's owned by cocoaEvent but this is released with ARC anyway
        } else{
            event=i==4?CGEventCreateMouseEvent(nullptr,mouseButton,pos,(CGMouseButton)0):CGEventCreateKeyboardEvent(nullptr,key,isPressed);
            CGEventPost(kCGHIDEventTap,event); // post event
            CFRelease(event); // release event for memory management
        }
    }

    //// this block can be moved wherever, it logs how much memory is currently being used by the program
    // mach_task_basic_info_data_t info;
    // mach_msg_type_number_t count=MACH_TASK_BASIC_INFO_COUNT;
    // kern_return_t kr=task_info(mach_task_self(),MACH_TASK_BASIC_INFO,(task_info_t)&info,&count); // get memory being used in bytes
    // if (kr==KERN_SUCCESS){
    //     char mem[18];
    //     snprintf(mem,18,"%f",(double)info.resident_size/1024); // convert to KB, convert to string (char[])
    //     for (int i=strlen(mem)-1;i>0;i--){ // loop backwards through characters
    //         if (mem[i]=='0') {continue;} // skip zeros
    //         if (mem[i]=='.') {i--;} // if first non-zero is decimal point, skip that too
    //         mem[i+1]='\0'; // cut off end of string just after this character
    //         break; // breaks loop on first character that isnt a zero
    //     }
    //     NSLog(@"Current memory used: %sKB",mem); // log as dynamic float/int representations
    // } else {
    //     NSLog(@"Failed to get task info: %i",kr);
    // }
    //// end of memory usage log
}
@end

class BLEScanner{
public:
    BLEScanner(){ // constructor
        delegate=[BLEDelegate new]; // instantiates delegate object from objc class BLEDelegate
        // delegate.scanner=this; // sets itself as an attribute of delegate object, commented cause it's not necessary yet but may be useful later
        centralManager=[[CBCentralManager alloc] initWithDelegate:delegate queue:nil]; // create CBCentralManager object with BLEDelegate object, also calls centralManagerDidUpdateState
    }

    ~BLEScanner(){ // destructor
        NSLog(@"I don't think this bit ever runs in the current version of the app");
        [centralManager release]; // tells compiler that BLEScanner object is no longer using centralManager object
        [delegate release]; // if no other objects still using then it's deallocated & memory is freed (in this case immediately)
    }
private:
    CBCentralManager* centralManager; // declare attributes defined in constructor
    BLEDelegate* delegate;
};

int main(){
    @autoreleasepool{ // manages memory pool for objc objects, in this case I think just for NSRunLoop
        BLEScanner scanner; // initiallise BLEScanner which initialises CBCentralManager which calls centralManagerDidUpdateState which calls scanForPeripheralsWithServices
        [[NSRunLoop currentRunLoop] run]; // gets current running thread (scanForPeripheralsWithServices) & runs in an infinite loop so the program doesn't terminate before the scan gets anything
        // when the scan finds peripherals it calls didDiscoverPeripheral which calls the next method & so on
    }
    NSLog(@"I don't think this bit ever runs in the current version of the app either");
    return 0;
}

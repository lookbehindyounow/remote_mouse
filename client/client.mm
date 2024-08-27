// IMPORTANT RULE WITH NO EXAMPLE IN CODE: it's "self" in objc & "this" in c++
#import <Foundation/Foundation.h> // this has all the NS stuff, it's also "import" for objc libraries vs "include" for c++
#import <CoreBluetooth/CoreBluetooth.h> // macbook bluetooth api

// #include <mach/mach.h>
// // this block can be moved wherever, it logs how much memory is currently being used by the program
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
//     NSLog(@"Failed to get task info: %d",kr);
// }

// class BLEScanner; // declaring c++ class BLEScanner so it can be referenced in BLEDelegate, commented cause it's not currently being referenced in BLEDelegate

// objc class declaration, inherits from NSObject and CBCentralManagerDelegate & CBPeripheralDelegate protocols (protocol≈interface)
@interface BLEDelegate: NSObject <CBCentralManagerDelegate,CBPeripheralDelegate>
// nonatomic: not thread-safe, doesn't use any locks (faster)
// strong: strong reference, adds to reference count & effectively holds on to object so it isn't deallocated until it's no longer being used by holder
// weak: weak reference, doesn't add to reference count so it's not holding onto the object or preventing deallocation
// assign: like a weak reference but also for primitive types?
@property(nonatomic,strong) CBPeripheral* connectedPeripheral; // delagate needs to hold onto peripheral after discovering so it isn't released before it can connect
// @property(nonatomic,weak) BLEScanner* scanner; // for delegate object to contain a reference to the scanner, commented cause it's not necessary yet but may be useful later
// @property(nonatomic,assign) long timesConnected;
@property(nonatomic,assign) time_t connectionTime;
@end

@implementation BLEDelegate // objc class defenition/implementation
-(void)centralManagerDidUpdateState:(CBCentralManager*)central{ // "-" means instance level ("+" would be class level), argument "central" is a "CBCentralManager" pointer
    if (central.state==CBManagerStatePoweredOn){
        NSLog(@"Bluetooth is on. Starting scan...");
        // self.timesConnected=0; // for checking for memory leaks
        // methods in objc are referenced with their parameters inside the method name
        [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // objc method call: [object namePart1:arg1 namePart2:arg2];
        // [CBUUID UUIDWithString:@"4500"] is target service UUID, should make this more dynamic at some point
    } else{
        NSLog(@"Bluetooth is not available.");
    }
}

// objc method definition: +/-(return type)namePart1:(arg1Type)arg1... namePartN:(argNType)argN {implementation}, argTypes are pointers, primitives or structs
-(void)centralManager:(CBCentralManager*)central didDiscoverPeripheral:(CBPeripheral*)peripheral advertisementData:(NSDictionary<NSString*,id>*)advertisementData RSSI:(NSNumber*)RSSI{
    NSLog(@"Discovered device: %@, RSSI: %@",peripheral.name,RSSI);
    if ([peripheral.name isEqualToString:@"remote_mouse"]){
        [central stopScan];
        self.connectedPeripheral=peripheral; // for reference counting, if this peripheral isn't held onto it's deallocated after this method returns
        peripheral.delegate=self; // BLEDelegate inherits from CBCentralManagerDelegate & CBPeripheralDelegate protocols so can be used for both
        [central connectPeripheral:peripheral options:nil];
        NSLog(@"Connecting to %@",peripheral.name);
    }
}

-(void)centralManager:(CBCentralManager*)central didConnectPeripheral:(CBPeripheral*)peripheral{
    self.connectionTime=time(0);
    NSLog(@"Successfully connected to %@ server",peripheral.name);
    // start of memory usage log
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
    //     NSLog(@"Failed to get task info: %d",kr);
    // }
    // self.timesConnected++;
    // NSLog(@"times connected: %ld",self.timesConnected); // log times connected to compare with current used memory size
    // end of memory usage log
    [peripheral discoverServices:nil];
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
        NSLog(@"    Characteristic UUID: %@",characteristic.UUID);
        // [peripheral readValueForCharacteristic:characteristic];
        [peripheral setNotifyValue:true forCharacteristic:characteristic];
    }
}

-(void)peripheral:(CBPeripheral*)peripheral didUpdateValueForCharacteristic:(CBCharacteristic*)characteristic error:(NSError*)error{
    if (error){
        NSLog(@"Error receiving notification for characteristic %@: %@",characteristic.UUID,error.localizedDescription);
        return;
    }
    short bytes;
    memcpy(&bytes,[characteristic.value bytes],2); // put raw bytes from characteristic.value's property "bytes" into a short (cause it's 2 bytes)
    char bits[16];
    for (short i=0;i<16;i++){
        bits[i]=bytes&(32768>>i)?'1':'0'; // for each bit in "bytes", add a 1 or 0 to binary string "bits"
    }
    char x[6];char y[6];char buttons[7];
    strncpy(x,bits,5);strncpy(y,bits+5,5);strncpy(buttons,bits+10,6); // split bits up into sections for x, y & buttons
    x[5]='\0';y[5]='\0';buttons[6]='\0';
    NSLog(@"Characteristic data: %s %s %s",x,y,buttons); // display bits with spaces between sections
}

-(void)centralManager:(CBCentralManager*)central didFailToConnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"Failed to connect to %@, error: %@",peripheral.name,error.localizedDescription);
    NSLog(@"Was connecting for %lds",(long)(time(0)-self.connectionTime));
    // self.connectedPeripheral=nil;
    // [peripheral release];
    [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // restart scan
}

-(void)centralManager:(CBCentralManager*)central didDisconnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"Disconnected from %@, error: %@",peripheral.name,error.localizedDescription);
    NSLog(@"Connected for %lds",(long)(time(0)-self.connectionTime));
    // self.connectedPeripheral=nil; // thought I would need these but was getting segmentation faults with either? test again
    // [peripheral release];
    [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // restart scan
}
@end

class BLEScanner{
public:
    BLEScanner(){ // constructor
        delegate=[BLEDelegate new]; // instantiates delegate object from objc class BLEDelegate
        // delegate.scanner=this; // sets itself as an attribute of delegate object, commented cause it's not necessary yet but may be useful later
        centralManager=[[CBCentralManager alloc] initWithDelegate:delegate queue:nil]; // allocates memory for & initialises CBCentralManager object with delegate object, also calls [delegate centralManagerDidUpdateState:self];
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
        BLEScanner scanner; // instantiate & initiallise scanner which does the same for delegate & centralManager which calls centralManagerDidUpdateState which calls scanForPeripheralsWithServices:options: on the centralManager
        [[NSRunLoop currentRunLoop] run]; // gets current running thread (scanForPeripheralsWithServices:options:) & runs in an infinite loop so the program doesn't terminate before the scan gets anything
        // when the scan finds peripherals it calls the second method on the delegate object with those 4 arguments
    }
    NSLog(@"I don't think this bit ever runs in the current version of the app either");
    return 0;
}

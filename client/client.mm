// IMPORTANT RULE WITH NO EXAMPLE IN CODE: it's "self" in objc & "this" in c++
#import <Foundation/Foundation.h> // this has all the NS stuff, it's also "import" for objc libraries vs "include" for c++
#import <CoreBluetooth/CoreBluetooth.h> // macbook bluetooth api

// #include <mach/mach.h>
// this block can be moved wherever, it logs how much memory is being used by the program
// mach_task_basic_info_data_t info;
// mach_msg_type_number_t count=MACH_TASK_BASIC_INFO_COUNT;
// kern_return_t kr=task_info(mach_task_self(),MACH_TASK_BASIC_INFO,(task_info_t)&info,&count);
// if (kr==KERN_SUCCESS) {
//     char mem[18];
//     snprintf(mem,18,"%f",((double)info.resident_size+51.2)/1024);
//     for (int i=strlen(mem)-1;i>0;i--){
//         if (mem[i]=='0') {continue;}
//         if (mem[i]=='.') {i--;}
//         mem[i+1]='\0';
//         break;
//     }
//     NSLog(@"%lu",strlen(mem));
//     NSLog(@"Current memory used: %sKB",mem);
// } else {
//     NSLog(@"Failed to get task info: %d",kr);
// }

// class BLEScanner; // declaring c++ class BLEScanner so it can be referenced in BLEDelegate, commented cause it's not currently being referenced in BLEDelegate

@interface BLEDelegate: NSObject <CBCentralManagerDelegate,CBPeripheralDelegate> // declaring objc class BLEDelegate which inherits from NSObject (normal objc object) & CBCentralManagerDelegate protocol (protocol≈interface)
@property(nonatomic,strong) CBPeripheral* connectedPeripheral; // delagate needs to hold onto peripheral (strong) after discovering so it isn't released before it can connect
// @property (nonatomic,weak) BLEScanner* scanner; // for delegate object to contain a reference to the scanner, commented cause it's not necessary yet but may be useful later
@property(nonatomic,assign) CBUUID* targetUUID;
// nonatomic: not thread-safe, doesn't use any locks; weak: weak reference, doesn't add to reference count so it's not holding onto the object & preventing deallocation
// @property (nonatomic,assign) long timesConnected;
@end

@implementation BLEDelegate // defining of objc class BLEDelegate's methods (implementations)
-(void)centralManagerDidUpdateState:(CBCentralManager*)central{ // "-" means instance level ("+" would be class level), argument "central" is a "CBCentralManager" pointer
    if (central.state==CBManagerStatePoweredOn){
        NSLog(@"Bluetooth is on. Starting scan...");
        // self.timesConnected=0;
        // methods in objc are referenced with their parameters inside the method name
        [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil]; // objc method being called --> [object namePart1:arg1 namePart2:arg2];
    } else{
        NSLog(@"Bluetooth is not available.");
    }
}

// methods in objc are referenced with their parameters inside the method name; objc method being defined --> +/- (return type)namePart1:(arg1Type, usually pointer)arg1... namePartN:(argNType, usually pointer)argN {implementation}
-(void)centralManager:(CBCentralManager*)central didDiscoverPeripheral:(CBPeripheral*)peripheral advertisementData:(NSDictionary<NSString*,id>*)advertisementData RSSI:(NSNumber*)RSSI {
    NSLog(@"Discovered device: %@, RSSI: %@",peripheral.name,RSSI);
    if ([peripheral.name isEqualToString:@"remote_mouse"]){
        [central stopScan];
        self.connectedPeripheral=peripheral; // for reference counting, if this peripheral isn't held onto it's deallocated after this method returns
        peripheral.delegate=self; // BLEDelegate inherits from CBCentralManagerDelegate & CBPeripheralDelegate protocols
        [central connectPeripheral:peripheral options:nil];
        NSLog(@"Connecting to %@", peripheral.name);
    }
}

-(void)centralManager:(CBCentralManager*)central didConnectPeripheral:(CBPeripheral*)peripheral{
    NSLog(@"Successfully connected to %@ server",peripheral.name);
    // start of memory usage log
    // mach_task_basic_info_data_t info;
    // mach_msg_type_number_t count=MACH_TASK_BASIC_INFO_COUNT;
    // kern_return_t kr=task_info(mach_task_self(),MACH_TASK_BASIC_INFO,(task_info_t)&info,&count);
    // if (kr==KERN_SUCCESS) {
    //     char mem[18];
    //     snprintf(mem,18,"%f",((double)info.resident_size+51.2)/1024);
    //     for (int i=strlen(mem)-1;i>0;i--){
    //         if (mem[i]=='0') {continue;}
    //         if (mem[i]=='.') {i--;}
    //         mem[i+1]='\0';
    //         break;
    //     }
    //     NSLog(@"%lu",strlen(mem));
    //     NSLog(@"Current memory used: %sKB",mem);
    // } else {
    //     NSLog(@"Failed to get task info: %d",kr);
    // }
    // self.timesConnected++;
    // NSLog(@"times connected: %ld",self.timesConnected);
    // end of memory usage log
    [peripheral discoverServices:nil];
}

-(void)peripheral:(CBPeripheral*)peripheral didDiscoverServices:(NSError*)error{ // badly named method from CoreBluetooth, services are in peripheral.services
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
    }
}

-(void)centralManager:(CBCentralManager*)central didFailToConnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"Failed to connect to %@, error: %@",peripheral.name,error.localizedDescription);
    // self.connectedPeripheral=nil;
    // [peripheral release];
    [central scanForPeripheralsWithServices:nil options:nil]; // restart scan
}

-(void)centralManager:(CBCentralManager*)central didDisconnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"Disconnected from %@, error: %@",peripheral.name,error.localizedDescription);
    // self.connectedPeripheral=nil;
    // [peripheral release];
    [central scanForPeripheralsWithServices:nil options:nil]; // restart scan
}
@end

class BLEScanner{ // defining c++ class BLEScanner's methods
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

// Usage Example
int main(){
    @autoreleasepool{ // manages memory pool for objc objects, in this case I think just for NSRunLoop
        BLEScanner scanner; // instantiate & initiallise scanner which does the same for delegate & centralManager which calls centralManagerDidUpdateState which calls scanForPeripheralsWithServices:options: on the centralManager
        [[NSRunLoop currentRunLoop] run]; // gets current running thread (scanForPeripheralsWithServices:options:) & runs in an infinite loop so the program doesn't terminate before the scan gets anything
        // when the scan finds peripherals it calls the second method on the delegate object with those 4 arguments
    }
    return 0; // I don't think this ever runs since the NSRunLoop thing would only stop if it threw an error but not sure
}

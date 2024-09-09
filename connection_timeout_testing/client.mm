#import <Foundation/Foundation.h>
#import <CoreBluetooth/CoreBluetooth.h>
#include <cstring>
#include <ctime>

@interface BLEDelegate: NSObject <CBCentralManagerDelegate,CBPeripheralDelegate>
@property(nonatomic,strong) CBPeripheral* connectedPeripheral;
@property(atomic,assign) int connectionAttemptNumber;
@property(nonatomic,assign) int connectionTime;
@end

@implementation BLEDelegate
-(instancetype)init{
    self=[super init];
    self.connectionAttemptNumber=0;
    return self;
}

-(void)centralManagerDidUpdateState:(CBCentralManager*)central{
    if (central.state==CBManagerStatePoweredOn){
        [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil];
        NSLog(@"Scanning...");
    }
}

-(void)centralManager:(CBCentralManager*)central didDiscoverPeripheral:(CBPeripheral*)peripheral advertisementData:(NSDictionary<NSString*,id>*)advertisementData RSSI:(NSNumber*)RSSI{
    if ([peripheral.name isEqualToString:@"remote_mouse"]){
        [central stopScan];
        peripheral.delegate=self;
        NSLog(@"Connecting...");
        [central connectPeripheral:peripheral options:nil];
        self.connectionAttemptNumber++;
        self.connectedPeripheral=peripheral;
    }
}

-(void)centralManager:(CBCentralManager*)central didConnectPeripheral:(CBPeripheral*)peripheral{
    self.connectionTime=time(0);
    [peripheral discoverServices:nil];
}

-(void)peripheral:(CBPeripheral*)peripheral didDiscoverServices:(NSError*)error{
    [peripheral discoverCharacteristics:nil forService:peripheral.services[0]];
}

-(void)peripheral:(CBPeripheral*)peripheral didDiscoverCharacteristicsForService:(CBService*)service error:(NSError*)error{
    [peripheral setNotifyValue:true forCharacteristic:service.characteristics[0]];
    NSLog(@"Subscribed");
    // int thisAttempt=self.connectionAttemptNumber;
    // dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(5e9)),dispatch_get_main_queue(),^{ // attempt at a keep alive method
    //     if (self.connectionAttemptNumber==thisAttempt && peripheral.state==2){ // if this attempt still connected after 10s
    //         short data=0;
    //         NSLog(@"0");
    //         [peripheral writeValue:[NSData dataWithBytes:&data length:2] forCharacteristic:service.characteristics[0] type:CBCharacteristicWriteWithResponse];
    //         NSLog(@"1");
    //         [peripheral readValueForCharacteristic:characteristic]
    //     }
    // });
}

-(void)peripheral:(CBPeripheral*)peripheral didUpdateValueForCharacteristic:(CBCharacteristic*)characteristic error:(NSError*)error{
    short data;
    memcpy(&data,[characteristic.value bytes],2);
    char bits[17];
    for (short i=0;i<16;i++){
        bits[i]=data&(32768>>i)?'1':'0';
    }
    bits[16]='\0';
    NSLog(@"%s",bits);
}

-(void)centralManager:(CBCentralManager*)central didDisconnectPeripheral:(CBPeripheral*)peripheral error:(NSError*)error{
    NSLog(@"Disconnected from %@ server",peripheral.name);
    error?NSLog(@"Error: %@",error.localizedDescription):
    NSLog(@"Connected for %lis",time(0)-self.connectionTime);
    self.connectedPeripheral=nil;
    NSLog(@"Scanning...");
    [central scanForPeripheralsWithServices:@[[CBUUID UUIDWithString:@"4500"]] options:nil];
}
@end

class BLEScanner{
public:
    BLEScanner(){
        delegate=[BLEDelegate new];
        centralManager=[[CBCentralManager alloc] initWithDelegate:delegate queue:nil];
    }
private:
    CBCentralManager* centralManager;
    BLEDelegate* delegate;
};

int main(){
    @autoreleasepool{
        BLEScanner scanner;
        [[NSRunLoop currentRunLoop] run];
    }
    return 0;
}

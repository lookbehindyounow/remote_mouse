#import <Foundation/Foundation.h>
#import <CoreBluetooth/CoreBluetooth.h>

// IMPORTANT RULE WITH NO EXAMPLE IN CODE: it's "self" in objc & "this" in c++

class BLEScanner; // declaring c++ class BLEScanner so it can be referenced in BLEDelegate

@interface BLEDelegate : NSObject <CBCentralManagerDelegate> // declaring objc class BLEDelegate which inherits from NSObject (normal objc object) & CBCentralManagerDelegate protocol (protocol≈interface)
@property (nonatomic, assign) BLEScanner* scanner;
@end

@implementation BLEDelegate // defining of objc class BLEDelegate's methods (implementations)
// methods in objc are referenced with multiple names for each of their parameters (horrifying)
- (void)centralManagerDidUpdateState:(CBCentralManager *)central { // "-" means instance level (not class level), argument "centralManagerDidUpdateState" is a "CBCentralManager" pointer that's locally called "central"
    if (central.state == CBManagerStatePoweredOn) {
        NSLog(@"Bluetooth is on. Starting scan...");
        [central scanForPeripheralsWithServices:nil options:nil]; // objc method being called --> [object arg1name:arg1 arg2name:arg2];
    } else {
        NSLog(@"Bluetooth is not available.");
    }
}
- (void)centralManager:(CBCentralManager *)central didDiscoverPeripheral:(CBPeripheral *)peripheral advertisementData:(NSDictionary<NSString *,id> *)advertisementData RSSI:(NSNumber *)RSSI {
    NSLog(@"Discovered device: %@, RSSI: %@", peripheral.name, RSSI);
    // handle discovered device here
}
@end

class BLEScanner { // defining c++ class BLEScanner's methods
public:
    BLEScanner() { // constructor
        delegate = [BLEDelegate new]; // instantiates delegate object from objc class BLEDelegate
        // delegate.scanner = this; // sets itself as an attribute of delegate object, commented cause it's not necessary yet but may be useful later
        centralManager = [[CBCentralManager alloc] initWithDelegate:delegate queue:nil]; // allocates memory for & initialises CBCentralManager object with delegate object, also calls [delegate centralManagerDidUpdateState:self];
    }

    ~BLEScanner() { // destructor (the fuck)
        [centralManager release]; // tells compiler that BLEScanner object is no longer using centralManager object
        [delegate release]; // if no other objects still using then it's deallocated & memory is freed (in this case immediately)
    }

private:
    CBCentralManager* centralManager; // declare attributes defined in constructor
    BLEDelegate* delegate;
};

// Usage Example
int main() {
    @autoreleasepool { // manages memory pool for objc objects, in this case I think just for NSRunLoop
        BLEScanner scanner; // instantiate & initiallise scanner which does the same for delegate & centralManager which calls centralManagerDidUpdateState which calls scanForPeripheralsWithServices on the centralManager
        [[NSRunLoop currentRunLoop] run]; // gets current running thread & runs in an infinite loop so the program doesn't terminate before the scan gets anything
        // when the scan finds peripherals it calls the second method on the delegate object with those 4 arguments
    }
    return 0; // I don't think this ever runs since the NSRunLoop thing would only stop if it threw an error but not sure
}

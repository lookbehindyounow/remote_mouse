## Remote Mouse
App to control a macbook with an android app via bluetooth low energy

Using python with kivy for mobile app, pyjnius & a bit of java to communicate with android bluetooth api, objective-c++ for the macbook app using CoreBluetooth for the bluetooth client & ApplicationServices to simulate the input

compile on mac with:
clang++ -std=c++17 -o client client.mm -framework Foundation -framework CoreBluetooth -framework ApplicationServices -framework AppKit

then run with ./client
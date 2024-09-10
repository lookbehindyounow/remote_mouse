# Remote Mouse
### This an android app that you can use to control a macbook via bluetooth low energy
You can move the mouse, left/right click, press arrow keys, raise & lower volume, scroll up & down and even scroll sideways between fullscreen apps as if you're doing the 3 finger swipe on the trackpad; the last two you can do by holding shift & swiping on the mousepad. The controls are pretty smooth & all of the data is sent in one 16-bit characteristic via notifications that only send when you actually do something on the android app so it's very lightweight.\
The android app was made in python with kivy, using pyjnius & a smidgen of java to communicate with android bluetooth api. The macbook app is in objective-c++ using CoreBluetooth for the bluetooth client & ApplicationServices to simulate the input.

Build android app with:\
buildozer android debug\
Compile on mac with:\
clang++ -std=c++17 -o client client.mm -framework Foundation -framework CoreBluetooth -framework ApplicationServices -framework AppKit\

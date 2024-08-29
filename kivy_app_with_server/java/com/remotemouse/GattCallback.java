package com.remotemouse;

import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServer; // this can go if we don't need read requests
import android.bluetooth.BluetoothGattService; // probably don't need
import android.bluetooth.BluetoothGattCharacteristic; // this can go if we don't need read requests
import com.remotemouse.IJavaMessenger; // may ot need this cause it's same package

public class GattCallback extends BluetoothGattServerCallback{
    public BluetoothDevice device; // need the connected device to send notifications to; accessed in the python
    public IJavaMessenger javaMessenger;
    private BluetoothGattServer gattServer; // need the server to respond to read requests
    public GattCallback(IJavaMessenger javaMessenger){
        System.out.println("HERE3 GattCallback constructor running");
        this.javaMessenger=javaMessenger;
    }
    
    @Override // does this also run on disconnect or is there another method to extend?
    public void onConnectionStateChange(BluetoothDevice device, int status, int newState){
        this.javaMessenger.callInPython("device: "+device+", status: "+status+", new state: "+newState);
        this.device=device;
    }

    public void setServer(BluetoothGattServer gattServer){ // this method used in the python
        this.gattServer=gattServer;
    }
    @Override // unsure if necessary for notifications, wouldn't need server here either if it's not
    public void onCharacteristicReadRequest(BluetoothDevice device, int requestId, int offset, BluetoothGattCharacteristic characteristic){
        this.gattServer.sendResponse(device, requestId, 0, offset, characteristic.getValue());
    }
}
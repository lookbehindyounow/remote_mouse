package com.remotemouse;

import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServer; // this can go if we don't need read requests
import android.bluetooth.BluetoothGattService; // probably don't need
import android.bluetooth.BluetoothGattCharacteristic; // this can go if we don't need read requests

public class GattCallback extends BluetoothGattServerCallback {
    public String message; // connection state; accessed in the python
    public BluetoothDevice device; // need the connected device to send notifications to; accessed in the python
    private BluetoothGattServer gattServer; // need the server to respond to read requests
    public GattCallback(){
        this.message="no devices attached yet";
    }
    
    @Override // does this also run on disconnect or is there another method to extend?
    public void onConnectionStateChange(BluetoothDevice device, int status, int newState) {
        this.message="device: "+device+", status: "+status+", new state: "+newState;
        this.device=device;
    }

    public void setServer(BluetoothGattServer gattServer) { // this method used in the python
        this.gattServer=gattServer;
    }
    @Override // unsure if necessary for notifications, wouldn't need server here either if it's not
    public void onCharacteristicReadRequest(BluetoothDevice device, int requestId, int offset, BluetoothGattCharacteristic characteristic) {
        this.gattServer.sendResponse(device, requestId, 0, offset, characteristic.getValue());
    }
}
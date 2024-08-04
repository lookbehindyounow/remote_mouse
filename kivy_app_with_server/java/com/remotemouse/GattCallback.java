package com.remotemouse;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothGattServer;
import android.bluetooth.BluetoothGattService; // probably don't need
import android.bluetooth.BluetoothGattCharacteristic;

public class GattCallback extends BluetoothGattServerCallback {
    public String message;
    public BluetoothDevice device;
    private BluetoothGattServer gattServer;
    public GattCallback(){
        this.message="no devices attached yet";
    }
    
    @Override
    public void onConnectionStateChange(BluetoothDevice device, int status, int newState) {
        this.message="device: "+device+", status: "+status+", new state: "+newState;
        this.device=device;
    }

    public void addServer(BluetoothGattServer gattServer) { // the callback needs the server to respond to read requests
        this.gattServer=gattServer;
    }
    @Override
    public void onCharacteristicReadRequest(BluetoothDevice device, int requestId, int offset, BluetoothGattCharacteristic characteristic) {
        this.gattServer.sendResponse(device, requestId, 0, offset, characteristic.getValue());
    }
}
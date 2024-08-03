package com.remotemouse;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothGattService;

public class Callback extends BluetoothGattServerCallback {
    public String message;
    public Callback(){
        this.message="no devices attached yet";
    }
    
    @Override
    public void onConnectionStateChange(BluetoothDevice device, int status, int newState) {
        this.message="device: "+device+", status: "+status+", new state: "+newState;
    }
}
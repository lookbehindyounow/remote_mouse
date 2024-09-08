package com.remotemouse;

import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServer;
import android.bluetooth.BluetoothGattCharacteristic;

public class GattCallback extends BluetoothGattServerCallback{
    public BluetoothDevice device;
    private BluetoothGattServer gattServer;
    public GattCallback(){
        this.device=null;
    }
    
    @Override
    public void onConnectionStateChange(BluetoothDevice device, int status, int newState){
        System.out.println("newState: "+newState+" device: "+device+" status: "+status);
        this.device=device;
    }

    public void setServer(BluetoothGattServer gattServer){
        this.gattServer=gattServer;
    }

    @Override
    public void onCharacteristicReadRequest(BluetoothDevice device, int requestId, int offset, BluetoothGattCharacteristic characteristic){
        this.gattServer.sendResponse(device, requestId, 0, offset, characteristic.getValue());
    }
}
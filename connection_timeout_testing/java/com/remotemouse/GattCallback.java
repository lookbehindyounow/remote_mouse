package com.remotemouse;

import android.bluetooth.BluetoothGattServerCallback;

import java.util.Arrays;
import java.util.UUID;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServer;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGatt;

public class GattCallback extends BluetoothGattServerCallback{
    public BluetoothDevice device;
    private BluetoothGattServer gattServer;
    public GattCallback(){
        this.device=null;
        System.out.println("HERE4");
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

    @Override
    public void onDescriptorWriteRequest(BluetoothDevice device, int requestId, BluetoothGattDescriptor descriptor,
    boolean preparedWrite, boolean responseNeeded, int offset, byte[] value) {
        gattServer.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, offset, value);
    }
}
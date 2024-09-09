package com.remotemouse;

import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServer;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGatt;

public class GattCallback extends BluetoothGattServerCallback{
    public BluetoothDevice device; // need the connected device to send notifications to; accessed in the python
    public IJavaMessenger javaMessenger; // interface declared in java implemented in python to trigger python events from onConnectionStateChange
    private BluetoothGattServer gattServer; // need the server to send the response to the write request to the CCCD
    public GattCallback(IJavaMessenger javaMessenger){
        this.javaMessenger=javaMessenger;
        this.device=null;
    }
    public void setServer(BluetoothGattServer gattServer){ // this method called from python after creating server
        this.gattServer=gattServer;
    }
    
    @Override
    public void onConnectionStateChange(BluetoothDevice device, int status, int newState){
        String message="";
        if (status!=0){
            message+="Unexpected status code "+status+"; ";
        }
        switch (newState){
            case 0:
                message+="Disconnected from";
                this.device=null;
                break;
            case 1:
                message+="Connecting to";
                break;
            case 2:
                message+="Connected to";
                this.device=device;
                break;
            case 3:
                message+="Disconnecting from";
                break;
        }
        message+=" device with address: "+device;
        this.javaMessenger.callInPython(message);
    }

    @Override // needed for client to receive confirmation after writing to CCCD (CCCD value doesn't actually need to be updated)
    public void onDescriptorWriteRequest(BluetoothDevice device, int requestId, BluetoothGattDescriptor descriptor, boolean preparedWrite, boolean responseNeeded, int offset, byte[] value){
        gattServer.sendResponse(device,requestId,BluetoothGatt.GATT_SUCCESS,offset,value);
    }
}
package com.remotemouse;

import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattServer; // not required for client to receive notifcations
import android.bluetooth.BluetoothGattCharacteristic; // not required for client to receive notifcations

public class GattCallback extends BluetoothGattServerCallback{
    public BluetoothDevice device; // need the connected device to send notifications to; accessed in the python
    public IJavaMessenger javaMessenger; // interface declared in java implemented in python to trigger python events from onConnectionStateChange
    private BluetoothGattServer gattServer; // not required for client to receive notifcations
    public GattCallback(IJavaMessenger javaMessenger){
        this.javaMessenger=javaMessenger;
        this.device=null;
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

    public void setServer(BluetoothGattServer gattServer){ // this method used in the python as server doesn't exist at time of initialisation
        this.gattServer=gattServer; // not required for client to receive notifcations
    }

    @Override // onCharacteristicReadRequest not required for client to receive notifcations
    public void onCharacteristicReadRequest(BluetoothDevice device, int requestId, int offset, BluetoothGattCharacteristic characteristic){
        this.gattServer.sendResponse(device, requestId, 0, offset, characteristic.getValue());
    }
}
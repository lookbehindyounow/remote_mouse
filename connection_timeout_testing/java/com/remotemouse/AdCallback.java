package com.remotemouse;

import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseSettings;

public class AdCallback extends AdvertiseCallback{
    @Override
    public void onStartSuccess(AdvertiseSettings settings){
        System.out.println("started advertising");
    }
    @Override
    public void onStartFailure(int errorCode){
        System.out.println("couldn't start advertising, error code: "+String.valueOf(errorCode));
    }
}
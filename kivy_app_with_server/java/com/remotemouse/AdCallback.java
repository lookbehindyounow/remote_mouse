package com.remotemouse;

import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseSettings;

public class AdCallback extends AdvertiseCallback{
    public String message;
    public AdCallback(){
        this.message="service not advertised yet";
    }

    @Override
    public void onStartSuccess(AdvertiseSettings settings){
        super.onStartSuccess(settings); // may not be necessary
        this.message="started advertising";
    }
    @Override
    public void onStartFailure(int errorCode){
        super.onStartFailure(errorCode); // may not be necessary
        this.message="couldn't start advertising, error code: "+String.valueOf(errorCode);
    }
}
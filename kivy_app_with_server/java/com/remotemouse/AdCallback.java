package com.remotemouse;

import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseSettings;

public class AdCallback extends AdvertiseCallback{
    public IJavaMessenger javaMessenger;
    public AdCallback(IJavaMessenger javaMessenger){
        this.javaMessenger=javaMessenger;
    }

    @Override
    public void onStartSuccess(AdvertiseSettings settings){ // may not be requested settings
        this.javaMessenger.callInPython("started advertising");
    }
    @Override
    public void onStartFailure(int errorCode){
        this.javaMessenger.callInPython("couldn't start advertising, error code: "+String.valueOf(errorCode));
    }
}
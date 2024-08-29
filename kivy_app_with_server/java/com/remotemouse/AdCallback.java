package com.remotemouse;

import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseSettings;
import com.remotemouse.IJavaMessenger; // may ot need this cause it's same package

public class AdCallback extends AdvertiseCallback{
    public IJavaMessenger javaMessenger;
    public AdCallback(IJavaMessenger javaMessenger){
        this.javaMessenger=javaMessenger;
    }

    @Override
    public void onStartSuccess(AdvertiseSettings settings){
        super.onStartSuccess(settings); // may not be necessary
        this.javaMessenger.callInPython("started advertising");
    }
    @Override
    public void onStartFailure(int errorCode){
        super.onStartFailure(errorCode); // may not be necessary
        this.javaMessenger.callInPython("couldn't start advertising, error code: "+String.valueOf(errorCode));
    }
}
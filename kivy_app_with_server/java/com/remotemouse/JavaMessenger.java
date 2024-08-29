package com.remotemouse;

import com.remotemouse.IJavaMessenger;

public class JavaMessenger implements IJavaMessenger{
    public void callInPython(String message){
        System.out.println(message);
    }
}
package com.example;

import com.example.IPrint;

public class Print implements IPrint{
    public void jprint(String message){
        System.out.println(message);
    }
}
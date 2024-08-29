package com.example;
import com.example.IPrint;

public class Holder{
    public IPrint printer;
    public Holder(IPrint printer){
        this.printer=printer;
    }
    public void jprint(String message){
        this.printer.jprint(message);
    }
}
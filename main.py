import time
import math
import RPi.GPIO as GPIO
import json
import sys
import os
import socketio
import serial
import subprocess
from datetime import *
import time
from datetime import datetime
import pathlib
import functions
import statistics
import numpy as np

sio = socketio.Client()
sio.connect('http://localhost:3000')

global halt_test
global ser
#/dev/ttyS0
ser = serial.Serial(
  
   port='/dev/ttyAMA0',
   baudrate = 115200,
   parity=serial.PARITY_NONE,
   stopbits=serial.STOPBITS_ONE,
   bytesize=serial.EIGHTBITS,
   timeout=1
)


@sio.on('connect')
def on_connect():
    print('connection established')

@sio.on('__INIT_TEST')
def message(data):
    print('starting Electrolysis')
    print(data)
    global filename
    global halt_test
    global decomp_value
    global water_conc
    global concentration
    global amperage
    global start_test
    global pause
    global water_conc2
    global polarity
    global element_name
    global chemical_symbol

    ###Extracting the electrolysis values from the UI and passing it to start Electrolysis function.
    decomp_value=float(data['decomposition'])
    print(decomp_value)
    water_conc=float(data['volume'])
    concentration=float(data['concentration'])
    polarity=int(data['polarity'])
    amperage=float(data['max_amps'])
    element_name=str(data['element_name'])
    chemical_symbol = str(data['chemical_symbol'])
    print(amperage,polarity)
    water_conc2=water_conc
    start_test(amperage,polarity)
    
    filename = functions.filename()
    halt_test= True

    init_test(decomp_value,water_conc ,concentration , ser,element_name)

###function to send command to STM32 to start electrolysis.
def start_test(amperage,polarity):
    x=amperage
    y=polarity
    for x in range(2):
        ser.write((b"ST"))
        ser.write((b"S"))
        ser.write((str(x).encode()))
        ser.write((b" "))
        ser.write((str(y).encode()))

###function to start electrolysis, recieves current values from PCB and sends to UI.
def init_test(decomp_value1,water_conc1,concentration1,ser,element_name):
    global halt_test
    global current_As
    global current_counter
    global current_f
    global current_sno
    global filename
    global path
    global start_time
    global current_excretion
    global current_conc
    global polarity
    global elapsed
    global elspased1
    global rem
    global remtime
    global last_time_rem
    
    start_time= functions.getdatetime()
    ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )
    counter=1
    global rem
    rem=[]
    remtime=0
    f=0
    As=0
    sno=1
    decomp=  decomp_value1
    water_conc = water_conc1
    last_time_rem=0
    while True:
        
        if halt_test:
            
            
            if(ser.in_waiting>1):
                x=ser.readline()
                d=x.decode()
                e=float(d[0:5])
                f +=e
                current_f = f
              
                if counter ==20 :
                 
                   y=f/20
                   if y>0:
                       remtime = remtime+1                   
                       rem.append(round(y,3))
                   y1=round(np.mean(rem),3)
                   counter=0
                   As +=round(y,3)
                   current_As=As
                   excretion = round((As / decomp),3)
                   current_excretion=excretion
                   conc= round((excretion /  water_conc),3)
                   current_conc=conc
                   if y1<= 0:
                       time_rem=0

                   else:

                       time_rem = (((decomp_value*water_conc*concentration1)/y1)-remtime)

                   if y<=0:
                       time_remaining=functions.GetTime(last_time_rem)
                   elif time_rem>0 and y>0:
                       time_remaining=functions.GetTime(time_rem)
                       last_time_rem=time_rem
                   elif time_rem<=0:
                       time_remaining=functions.GetTime(0)
                    

                   elapsed=functions.GetTime(sno)
                   elapsed1=elapsed
                   data= {
                        'qty_of_electricity' : ("%.2f" % round(As,2)),
                        'excretion' :("%.2f" % round(excretion,2)),
                        'concentration' : ("%.2f" % round(conc,2)),
                        'amperage' : ("%.3f" % round(y,3)),
                        'time_remaining': time_remaining,
                        'time_elapsed' : elapsed
                        }
                   sno +=1
                   current_sno = sno
                   
                 
##                   print(data)
                   sio.emit("__RESULTS",data)
                   
                   f=0
                   path="/home/pi/colloid-generator/electrolysis/tests/%s.txt" %filename  

                                          
                   if As>= (decomp_value1*water_conc1*concentration1) :  ## (decomp_value1*water_conc1*concentration1)
                    for x in range(4):
                        
                        ser.write((b"ST"))
                        ser.write((b"E"))
                        ser.write((b"0.0"))
                        ser.write((b" "))
                        ser.write((b"00"))
                    end_time= functions.getdatetime()
                    
                    data = {
                      'status': "Test Finished",
                      'final_results': { 
                      'element_name': element_name,
                      'chemical_symbol': chemical_symbol,
                      'volume': water_conc1,
                      'concentration': conc,
                      'excretion': excretion,
                      'qty_of_electricity': As,
                      'max_amps': amperage,
                      'polarity': polarity,
                      'time_elapsed': elapsed,
                      'date': str(datetime.now().year) + '-' + str(datetime.now().month) + '-' + str(datetime.now().day),
                      'time': time.asctime()[11:19]
                    }}
                    functions.log_data(path,filename,element_name,conc,water_conc1,polarity,start_time,end_time,elapsed,As,"Y")
                    try:
                        sio.emit('__RESULTS',data)
                    except Exception as e:
                        print("error while emitting test results for mail" , e)
                    break
                counter +=1
                current_counter= counter

        else:
##            current_sno=sno
            break

###Recieves resume command from the UI and calls the resume_test function.
@sio.on('__RESUME_TEST')
def on_message(data):
    print('Resuming test')
    global filename
    global halt_test
    global decomp_value
    global water_conc
    global concentration
    global amperage
    global start_test
    global pause
    global water_conc2
    global polarity
    global element_name
    global chemical_symbol
    
    decomp_value=float(data['decomposition'])
    print(decomp_value)
    water_conc=float(data['volume'])
    concentration=float(data['concentration'])
    polarity=int(data['polarity'])
    amperage=float(data['max_amps'])
    element_name=str(data['element_name'])
    water_conc2=water_conc
    start_test(amperage,polarity)
    
    halt_test= True
    resume_test(decomp_value,water_conc ,concentration , ser,element_name)

###function to resume electrolysis (if stopped from UI), recieves current values from PCB and sends to UI.
def resume_test(decomp_value1,water_conc1,concentration1,ser,element_name):
    global filename
    global halt_test
    global current_As
    global current_counter
    global current_f
    global current_sno
    global path
    global start_time
    global current_excretion
    global current_conc
    global polarity
    global elapsed
    global elapsed1
    global rem
    global remtime
    global last_time_rem

    ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )
    
    rem2=[]
    counter=current_counter
    f=current_f
    As=current_As
    As_pause=current_As
    sno=current_sno
    decomp_value= decomp_value1 
    water_conc = water_conc1
    while True:

        if halt_test:
            
            
            if(ser.in_waiting>1):
                x=ser.readline()
                d=x.decode()
                e=float(d[0:5])
                f +=e
                current_f = f
                if counter ==20 :
                   y=f/20
                   if y>0:
                       rem2.append(round(y,3))
                       remtime = remtime+1
                   y3=round(np.mean(rem2),3)
                   counter=0
                   As +=round(y,3)
                   current_As=As
                   excretion = round((As / decomp_value),3)
                   current_excretion = excretion
                   if y3 <= 0 :
                       time_rem=0
                   else:
                       time_rem = ((((decomp_value*water_conc*concentration1)-As_pause)/y3)-remtime)

                   if y<=0:
                       time_remaining=functions.GetTime(last_time_rem)
                   elif time_rem>0 and y>0:
                       time_remaining=functions.GetTime(time_rem)
                       last_time_rem=time_rem
                   elif time_rem<=0:
                       time_remaining=functions.GetTime(0)
                   conc= round((excretion /  water_conc),3)
                   current_conc=conc
                   elapsed=functions.GetTime(sno)
                   data= {
                        'qty_of_electricity' : ("%.2f" % round(As,2)),
                        'excretion' : ("%.2f" % round(excretion,2)),
                        'concentration' :("%.2f" % round(conc,2)),
                        'amperage' : ("%.3f" % round(y,3)),
                        'time_remaining': time_remaining,
                        'time_elapsed' : elapsed
                        }
                 
                   sno +=1
                   current_sno = sno
##                   print(data)
                   sio.emit("__RESULTS",data)
                   f=0
                   path="/home/pi/colloid-generator/electrolysis/tests/%s.txt" %filename  

                                          
                   if As>= (decomp_value*water_conc*concentration1) :  ## (decomp_value*water_conc*concentration1)
                       
                    for x in range(4):
                        
                        ser.write((b"ST"))
                        ser.write((b"E"))
                        ser.write((b"0.0"))
                        ser.write((b" "))
                        ser.write((b"00"))
                    end_time= functions.getdatetime()
                    data = {
                      'status': "Test Finished",
                      'final_results': { 
                      'element_name': element_name,
                      'chemical_symbol': chemical_symbol,
                      'volume': water_conc1,
                      'concentration': conc,
                      'excretion': excretion,
                      'qty_of_electricity': As,
                      'max_amps': amperage,
                      'polarity': polarity,
                      'time_elapsed': elapsed,
                      'date': str(datetime.now().year) + '-' + str(datetime.now().month) + '-' + str(datetime.now().day),
                      'time': time.asctime()[11:19]
                    }}
                    functions.log_data(path,filename,element_name,conc,water_conc,polarity,start_time,end_time,elapsed,As,"Y")
                    try:
                        sio.emit('__RESULTS', data)
                    except Exception as e:
                        print("error while emitting test results for mail" , e)
                    break
                counter +=1
                current_counter= counter

        else:
            
            break


###Recieves the STOP/PAUSE command from UI and calls the relevant function.
@sio.on('__HALT_TEST')
def on_message(data):
    print('HALT TEST')
    print(data)
    global halt_test
    
    
    try:
        halt_test= False
        if data['action']== 'stop':
            print('stopping test')
            stop_test(ser)
        if data['action']== 'pause':
            pause_test(ser)
        
    except Exception as e:
        print("Halt_Fail : ",e)

###Function to send stop command to STM32 to stop the electrolysis
def stop_test(ser):
    global path
    global start_time
    global water_conc2
    global polarity
    global element_name
    global elapsed
    global current_excretion
    global chemical_symbol
    global amperage
    global polarity
    global currnet_As
    global current_conc
    global filename
    for x in range(4):
        ser.write((b"ST"))
        ser.write((b"E"))
        ser.write((b"0.0"))
        ser.write((b" "))
        ser.write((b"00"))
    end_time= functions.getdatetime()
    data = {
      
      'element_name': element_name,
      'chemical_symbol': chemical_symbol,
      'volume': water_conc2,
      'concentration': current_conc,
      'excretion': current_excretion,
      'qty_of_electricity': current_As,
      'max_amps': amperage,
      'polarity': polarity,
      'time_elapsed': elapsed,
      'date': str(datetime.now().year) + '-' + str(datetime.now().month) + '-' + str(datetime.now().day),
      'time': time.asctime()[11:19]
    }
    try:
        functions.log_data(path,filename,element_name,current_conc,water_conc2,polarity,start_time,end_time,elapsed,current_As,"N")  
        sio.emit('__HALT_TEST',data)
        
    except Exception as e:
        print("error", e)

###Function to send pause command to STM32 to stop the electrolysis
def pause_test(ser):
    for x in range(4):
        ser.write((b"ST"))
        ser.write((b"E"))
        ser.write((b"0.0"))
        ser.write((b" "))
        ser.write((b"00"))


@sio.on('__IP')
def on_message(sid):
    ip_obj = functions.ip_address();
    print('IP Address ', ip_obj)
    sio.emit('__IP', ip_obj)

@sio.on('__RAM')
def on_message(sid):
    ram_obj = functions.ram()
    print('Memory Details ',ram_obj)
    sio.emit('__RAM', ram_obj)

@sio.on('__STORAGE')
def on_message(sid):
    storage_obj = functions.storage()
    print('Storage Details ',storage_obj)
    sio.emit('__STORAGE', storage_obj)

@sio.on('__ELEMENTS')
def message(sid):
    print(sid)
    data=functions.read_elements()
    sio.emit('__ELEMENTS', data)
    
@sio.on('__UPDATE_ELEMENT')
def on_message(sid, data):
##    print(sid, data)
    print("UPDATE-ELEMENT")
    element = data
    try:
        functions.update_elements(element)
        sio.emit('__UPDATE_ELEMENT', 'OK')
    except:
        sio.emit('__UPDATE_ELEMENT', 'Unable to update')
        print("Unable to Update")

@sio.on('__ADD_ELEMENT')
def on_message(sid, data):
##    print(sid, data)
    print("ADD ELEMENT")
    element = data
    try:
        functions.add_elements(element)
        sio.emit('__ADD_ELEMENT', 'OK')
    except:
        sio.emit('__ADD_ELEMENT', 'Unable to ADD')
        print("Unable to ADD")

@sio.on('__DELETE_ELEMENT')
def on_message(sid, data):
##    print(sid, data)
    print("DELETE ELEMENT")
    element= data
    try:
        functions.delete_element(data)
        sio.emit('__DELETE_ELEMENT', 'OK')
    except:
        sio.emit('__DELETE_ELEMENT', 'Unable to DELETE')
        print("Unable to DELETE")





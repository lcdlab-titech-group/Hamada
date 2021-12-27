# -*- coding:utf-8 -*-
import serial
import sys
import threading
import datetime
import glob
import time
import signal
import os
from argparse import ArgumentParser
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt

# "S" command: To activate the specified device B.
#        S + The number of device B + The address of them
# "E" command: To correct offset of all device B.
#        E
# "V" command: To sepecify delay time for L command.
#        V + delay time [1 - 999ms]


#S_Cmd="S001001\r"
# V_Cmd = "V100\r"
E_Cmd = "E\r"
# intervalTimeToSave = 600  #Seconds  600 means 10 min.
saveDir = r"C:\Users\MOE HAMADA\Documents\pyscripts_402"
debugFlag = False
# ComPort = "COM5"
zeroCorrectTime = "23:0:0"

class serialCom():

    def __init__(self):
    	
        print("init")
        print(ComPort)
        #self.getAvailablePort()
        self.portName = ComPort
        
        self.openSerialPort()

        self.ser.write(b"Q\r")
        self.ser.write(b"Q\r")
        self.ser.write(b"Q\r")
        print("Cmd:","Q")

        self.S_Num = int(S_Cmd[1:4])
        self.ser.write(bytes(S_Cmd,"utf-8"))
        print("Cmd:",S_Cmd)
    
        self.ser.write(bytes(V_Cmd,"utf-8"))
        self.ser.write(b"E\r")
        print("E-command")
        while True:
            readdata = self.ser.readline()
            data = readdata.decode('utf-8')
            if data != "":      # return = "done"
                break
        print("read = %s"%data)

        # thread start!!
        self.stop_event = threading.Event()
        self.recvT = threading.Thread(target=self.recvThread)
        self.recvT.setDaemon(True)   # スレッドをデーモン化
        self.recvT.start()
        self.ser.write(b"L\r")
        
        while True:
            try:
                time.sleep(0.0001)
            except KeyboardInterrupt:
                print('Ctrl-C interrupted!')  # Cntl-C 捕獲
                self.stop()
                sys.exit()


    def openSerialPort(self):
        self.ser = serial.Serial(self.portName,115200,timeout=2)
        if self.ser.isOpen():
            print("Open:%s"%self.portName)
            now = datetime.datetime.now()
            now_str = str(now).replace(" ","_").replace(":","")
            
            self.fd = open(saveDir +"/"+now_str+".csv",'w')
            #temp = open(saveDir +"/"+now_str+".csv_lock",'w')
            #temp.close()
            self.currentLockFileName = saveDir +"/"+now_str+".csv_lock"
            self.fileClosedTime= now
        else:
            print("Can't open the serial port.")
            exit(0)

    def zeroCorrectionCommand(self):
        self.ser.write(b"Q\r")
        self.ser.write(b"Q\r")
        self.ser.write(b"Q\r")
        self.ser.write(b"E\r")
        print("E-command")
        while True:    #wait "done" command
            readdata = self.ser.readline()
            data = readdata.decode('utf-8')            
            if data != "":
                break
        print("read = %s"%data)
        self.ser.write(b"L\r")

    def recvThread(self):
        print("Thread START")
        data=""
        while not self.stop_event.is_set():
            if self.ser.inWaiting() > 0:
                readdata = self.ser.readline()
                now = datetime.datetime.now()
                t = now.time()
                nowTime = str(t.hour) + ":" + str(t.minute) + ":" + str(t.second)
                #print("nowTime=[%s]"%nowTime)
                if nowTime == zeroCorrectTime:
                    self.zeroCorrectionCommand()

                if readdata != "":
                    try:
                        data = readdata.strip().decode('utf-8')
                        print("data=[%s]"%data)
                        data = data.replace("!", "")
                        data = data.split(",")
                        B_Address = int(data[0])
                        Sensor1 = int(data[1], base=16)
                        Sensor2 = int(data[2], base=16)
                        
                        self.fd.write("%s,%d,%d,%d\n"%(str(now),B_Address,Sensor1,Sensor2))
                        self.fd.flush()
                        if debugFlag:
                            sys.stdout.write("READ:%s,%d,%d,%d\n"%(str(now),B_Address,Sensor1,Sensor2))

                    except Exception as e:
                        print(u"例外args:", e.args)
                        print("Received data is invalid.")
                        print(data)
                        continue

                delta = now - self.fileClosedTime
                if delta.seconds >= intervalTimeToSave:
                    self.fd.close()
                    #os.remove(self.currentLockFileName)
                    now = datetime.datetime.now()
                    now_str = str(now).replace(" ","_").replace(":","")
                    self.fd = open(saveDir +"/"+now_str+".csv",'w')
                    #temp = open(saveDir+now_str +"/"+".csv_lock",'w')
                    #temp.close()
                    self.currentLockFileName = saveDir +"/"+now_str+".csv_lock"
                    self.fileClosedTime = now


    def stop(self):
        self.stop_event.set()
        self.recvT.join()
        self.ser.write(b"Q\r")
        print("Thread STOPED")
        self.ser.close()
        self.fd.close()
        #exit()


if __name__ == '__main__':

    arguments = sys.argv
    print(arguments[1])
    if len(arguments) > 1:
        if arguments[1] == "-v":
            debugFlag = True
   
    configFile = open("config.ini",'r')

    num = 1
    idList = "001"
    
    for line in configFile:
        line = line.replace("\n",":")
        items = line.split(":")
        if items[0] == "Port":
            ComPort = items[1]
        elif items[0] == "The number of B":
            num = int(items[1])
        elif items[0] == "The list of IDs":
            idList = items[1]
        elif items[0] == "The dir to Save":
            saveDir = items[1]
        elif items[0] == "Delay Time":
            V_Cmd = "V"+items[1]+"\r"
            print(V_Cmd)
        elif items[0] == "Interval time to save (sec)":
            intervalTimeToSave = int(items[1])

    S_Cmd = "S"+'{0:03d}'.format(num) + idList+"\r"
    print(S_Cmd)
    
    com = serialCom()

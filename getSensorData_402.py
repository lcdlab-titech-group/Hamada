# -*- coding:utf-8 -*-
import serial
import sys
import threading
import datetime
import time
import os
from serial.tools import list_ports


# "S" command: To activate the specified device B.
#        S + The number of device B + The address of them
# "E" command: To correct offset of all device B.
#        E
# "V" command: To sepecify delay time for L command.
#        V + delay time [1 - 999ms]


class serialCom():

    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baoudrate = baudrate
        self.ser.timeout = 2
        self.ser_port= self.select_port()
        self.stop_event = threading.Event()
        self.recvT = threading.Thread(target=self.recvThread)

    #COMポート番号は繋ぐたびに代わるので、スクリプト実行のたびに探索
    def select_port(self):
        ports = list_ports.comports() 
        devices = [info.device for info in ports]

        if len(devices) == 0:
            print("エラー: ポートが見つかりませんでした")
            return None
        elif len(devices) == 1:
            print(f"一つだけポートがありました {devices[0]}")
            self.ser.port = devices[0]
        else:
            # 複数ポートの場合、若いポートを選択
            print(f"ポートを複数検出 使用ポート：{devices[0]}")
            self.ser.port = devices[0]

        try:
            self.ser.open()
            return self.ser
        except:
            print("エラー：ポートが開けませんでした。")
            return None
        
    def OpenCSV(self):
        if self.ser_port.isOpen():
            now = datetime.datetime.now()
            now_str = str(now).replace(" ","_").replace(":","")    
            self.fd = open(saveDir +"/"+now_str+".csv",'w')
        
    def recvThread(self):
        print("Thread START")
        data=""
        while not self.stop_event.is_set():
            if self.ser_port.inWaiting() > 0:
                readdata = self.ser_port.readline()
                now = datetime.datetime.now()
                t = now.time()
                nowTime = str(t.hour) + ":" + str(t.minute) + ":" + str(t.second)
                if readdata != "":
                    try:
                        data = readdata.strip().decode('utf-8')
                        data = data.replace("!", "")
                        data = data.split(",")
                        B_Address = int(data[0])
                        Sensor1 = int(data[1], base=16)
                        Sensor2 = int(data[2], base=16)
                        
                        self.fd.write("%s,%d,%d,%d\n"%(str(now), B_Address, Sensor1, Sensor2))
                        self.fd.flush()
                        if debugFlag:
                            sys.stdout.write("READ:%s,%d,%d,%d\n"%(str(now), B_Address, Sensor1, Sensor2))

                    except Exception as e:
                        print(u"例外args:", e.args)
                        print("Received data is invalid.")
                        print(data)
                        continue

              
    def stop(self):
        self.stop_event.set()
        self.recvT.join()
        self.ser_port.write(b"Q\r")
        print("Thread STOPED")
        print("File saved")
        self.ser_port.close()
        self.fd.close()
        #exit()


if __name__ == '__main__':
    
    
    baudrate = 115200
    E_Cmd = "E\r"
    saveDir = r"C:\Users\MOE HAMADA\Documents\pyscripts_402"
    arguments = sys.argv
    
    
    # 「python getSensorData_******.py -v」と入力するとデバッグモードになり取得値が表示される
    debugFlag = False
    if len(arguments) > 1:
        if arguments[1] == "-v":
            debugFlag = True 
   
    configFile = open("config.ini",'r')
    
    for line in configFile:
        line = line.replace("\n",":")
        items = line.split(":")
        if items[0] == "The number of B":
            num = int(items[1])
        elif items[0] == "The list of IDs":
            idList = items[1]
        elif items[0] == "The dir to Save":
            saveDir = items[1]
        elif items[0] == "Delay Time":
            V_Cmd = "V"+items[1]+"\r"
            print(V_Cmd)
      
    S_Cmd = "S"+'{0:03d}'.format(num) + idList+"\r"
   
    
    
    com = serialCom()
    com.OpenCSV()
    S_Num = int(S_Cmd[1:4])
    com.ser_port.write(bytes(S_Cmd,"utf-8"))
    print("Cmd:",S_Cmd)
    com.ser_port.write(b"E\r")
    print("E-command")
    while True:
        readdata = com.ser_port.readline()
        data = readdata.decode('utf-8')
        if data != "":      # return = "done"
            break
  
    
    # thread start!!
    com.recvT.setDaemon(True)   # スレッドをデーモン化
    com.recvT.start()
    com.ser_port.write(b"L\r")
    while True:
            try:
                time.sleep(0.0001)
            except KeyboardInterrupt:
                print('Ctrl-C interrupted!')  # Cntl-C 捕獲
                com.stop()
                sys.exit()
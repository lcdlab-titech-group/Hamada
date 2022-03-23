# -*- coding:utf-8 -*-
import serial
import threading
import time
import os
import matplotlib.pyplot as plt
import numpy as np
from serial.tools import list_ports
import sys
import matplotlib.patches as patches
import math

class serialCom():
    
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baoudrate = baudrate
        self.ser.timeout = 2
        self.ser_port= self.select_port()
        self.stop_event = threading.Event()
        self.recvT = threading.Thread(target=self.DrawLine)

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

    def DrawLine(self):
        plt.ion()#インタラクティブに図を描画
        figure, ax = plt.subplots(figsize=(8,6))  
        t = [0] * 100
        y1 = [500] * 100
        y2 = [500] * 100
       
        li_L, = ax.plot(t, y1, linewidth = 3, label = "Sensor1")
        li_V, = ax.plot(t, y2, linewidth = 3, label = "Sensor2")
        plt.ylim(800, 1200)
        plt.xlabel("Time [s]")
        plt.ylabel("Sensor data [-]")
        Time = 0
        plt.legend()
        while not self.stop_event.is_set():
            Time += .1
            
            readdata = self.ser_port.readline()#センサ1の2軸センサ値を読み込む
            data = readdata.strip().decode('utf-8').replace("!", "").split(",")
            
            Sensor1_x = int(data[1], base=16)
            Sensor1_y = int(data[2], base=16)

            readdata = self.ser_port.readline()#センサ2の2軸センサ値を読み込む
            data = readdata.strip().decode('utf-8').replace("!", "").split(",")
            Sensor2_x = int(data[1], base=16)
            Sensor2_y = int(data[2], base=16)
            
            t.append(Time)#末尾に足して
            t.pop(0)#最初を消す
            y1.append(Sensor1_y)
            y1.pop(0)
            y2.append(Sensor2_y)
            y2.pop(0)
           
            li_L.set_xdata(t)#グラフの値更新
            li_L.set_ydata(y1)
            li_V.set_xdata(t)
            li_V.set_ydata(y2)

            plt.xlim(min(t), max(t))
            plt.ylim(min(min(y1, y2, key=min)) - 50, max(max(y1, y2, key=max)) + 50)

            figure.canvas.draw()
            figure.canvas.flush_events()
            time.sleep(.01)#待つ             

    def stop(self):
        self.stop_event.set()
        self.recvT.join()
        self.ser_port.write(b"Q\r")
        print("Thread STOPED")
        self.ser_port.close()
        #exit()
    
if __name__ == '__main__':
    
    baudrate = 115200
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
    S_Num = int(S_Cmd[1:4])
    com.ser_port.write(bytes(S_Cmd,"utf-8"))
    print("Cmd:",S_Cmd)
    com.ser.write(bytes(V_Cmd,"utf-8"))
    com.ser.write(b"Q\r")
    com.ser_port.write(b"E\r")#E-Command
    
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
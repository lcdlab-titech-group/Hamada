# -*- coding:utf-8 -*-
import serial
import sys
import threading
import datetime
import glob
import time
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math
from serial.tools import list_ports


def extractdata(Data1, Data2):
    n = 4
    num1 = np.where(Data1[n//2:-n//2] > 2)[0]
    num2 = np.where(Data2[n//2:-n//2] > 2)[0]

    a_1 = [i + n//2 for i in num1]
    a_2 = [i + n//2 for i in num2]
    maxdata1 = [0] * len(num1)
    maxdata2 = [0] * len(num2)
    
    b = Data1 + Data2
    for i, j in enumerate(a_1):
        x = (b[j - n//2: j + n//2])
        index = j - n // 2 + np.where(Data1[j - n // 2:j + n // 2] == max(Data1[j - n // 2:j + n // 2]))[0][0]
        if max(x) >= 8.:
            maxdata1[i] = index
    
    for i, j in enumerate(a_2):
        x = (b[j - n//2: j + n//2])
        index = j - n // 2 + np.where(Data2[j - n // 2:j + n // 2] == max(Data2[j - n // 2:j + n // 2]))[0][0]
        if max(x) >= 8.:
            maxdata2[i] = index
    t = list(set(maxdata1) | set(maxdata2))
    t = np.array(t)
    t = t[~(t == 0)]
    return t

def FindData(T1, T2, df, threshold_time_max, threshold_time_min):

    length1 = df[T1,1] / (df[T1,0] + df[T1,1])
    length2 = df[T2,1] / (df[T2,0] + df[T2,1]) 

    D, L = np.zeros((10), dtype = "float"), np.zeros((10), dtype = "float")
    count = 0   
    for t1_, l1 in zip(T1, length1):  
        if l1 > 0.01 and l1 < 1:
            during_time = (-t1_ + T2) / 10
            time_index = np.where((during_time <threshold_time_max) & (during_time > threshold_time_min)\
                                  & (length2 > 0.01) & (length2 < 1))[0]
            if len(time_index) != 0:
                T2_ = np.where(length2[time_index] == max(length2[time_index]))[0][0]
                D[count] = during_time[time_index][T2_]
                L[count] = -l1 + length2[time_index][T2_]
                count += 1

    return D[:count], L[:count]


E_Cmd = "E\r"
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

    def recvThread(self):
        flag = False
        plt.ion()    
        x,y = (0,0), (0,0)
        fig, ax = plt.subplots(figsize = (10,10))
        ax.add_patch(patches.Rectangle((0, 100 / math.sqrt(2)),100,1, fill= False, angle = -45))
        li, = plt.plot(x, y, linewidth = 5)
        plt.ylim(-50, 100)
        plt.xlim(-50, 100)
        y = np.zeros((100,2), dtype = 'float')
        time.sleep(1)
        while flag != True:
            try:
                for i in range(100):
                    readdata = self.ser.readline()
                    data1 = readdata.strip().decode('utf-8')
                    data1 = (data1.replace("!", "")).split(",")
                    s1_x = (int(data1[1], base=16) - 512) * (-0.16)
                    y[i,0] = (int(data1[2], base=16) - 512) * (-0.17)
                    readdata = self.ser.readline()
                    data2 = readdata.strip().decode('utf-8')
                    data2 = (data2.replace("!", "")).split(",")           
                    s2_x = (int(data2[1], base=16) - 512) * (0.15)
                    y[i,1] = (int(data2[2], base=16) - 512) * (-0.15)
                    g = y[i,1] / (y[i,0] + y[i,1]) * 100
                    g_x = - g / math.sqrt(2) + 100 / math.sqrt(2)
                    g_y = g / math.sqrt(2) 
                    f_x = (((s1_x + s2_x) / 2) - (y[i,0] + y[i,1])) / math.sqrt(2) 
                    f_y = - (((s1_x + s2_x) / 2) + (y[i,0] + y[i,1])) / math.sqrt(2)

                    newx, newy = (g_x,g_x + f_x), (g_y, g_y + f_y)
                    if abs(f_x) < 8 and abs(f_y) < 8:
                        newx, newy = (0,0), (0,0)
                        y[i,0], y[i,1] = 0,0

                    #図の更新、描画
                    li.set_xdata(newx)
                    li.set_ydata(newy)
                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    time.sleep(.01)#待つ               


                if np.any(y) != 0:
                    t = extractdata(y[:,0], y[:,1])
                    duration, l = FindData(t,t,y,2,0.5) 
                    V = l / duration * 1.1 
                    if len(V) > 0:
                        plt.text(0,0,"velocity = " + str(V[0])[:4] + "m/s", fontsize=50, bbox ={'facecolor':'azure', 'pad':10})
                    else:
                        plt.text(0,0,"Error2", fontsize=50, bbox ={'facecolor':'azure', 'pad':10})         
                else:
                     plt.text(0,0,"No data", fontsize=50, bbox ={'facecolor':'azure', 'pad':10})
                fig.canvas.draw()
                fig.canvas.flush_events()
                time.sleep(5)#待つ               
                break
            except Exception as e:
                print(u"例外args:", e.args)
                print("Received data is invalid.")
                continue

    def stop(self):
        self.stop_event.set()
        self.recvT.join()
        self.ser.write(b"Q\r")
        print("Thread STOPED")
        self.ser.close()
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
    com.ser_port.write(bytes(V_Cmd,"utf-8"))
    com.ser_port.write(b"Q\r")
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
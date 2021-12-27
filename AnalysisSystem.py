#!/usr/bin/env python
# coding: utf-8

# In[6]:


#②ある時間になったらデータ分析を行い結果を追記
import os
from glob import glob
import pandas as pd
import numpy as np
from zipfile import ZipFile
from io import BytesIO
from scipy import fftpack
import csv
from itertools import groupby
import matplotlib.pyplot as plt
import datetime
from PIL import Image

#指数表示をやめる
np.set_printoptions(suppress=True)

plt.rcParams['font.family'] = 'Meiryo' #全体のフォントを設定
plt.rcParams["font.size"] = 18

class ArrangeData():
    #最新のファイルを取ってくる関数
    def get_latest_file_path(self, dirname, i):
        target = os.path.join(dirname, '*')
        latest_modified_file_path = sorted(glob(target), key=lambda files: files[1])[-i]
        return latest_modified_file_path
    
    #fft＆データを整形する関数
    def fft(self, df):
        A_ = np.zeros((len(df) // 10 + 100, 12),dtype = 'float')
        for i in range(1, 7):
            pd_list = np.array(df[(df.iloc[:,1] == i)].iloc[:,2:4])
            for j in range(2):
                data = pd_list[:,j]
                sample_freq =fftpack.fftfreq(data.size,d= 1/10)
                sig_fft=fftpack.fft(data)
                pidxs = np.where(sample_freq > 0) 
                sig_fft[np.abs(sample_freq) > 1] = 0  
                sig_fft[np.abs(sample_freq) < 0.015] = 0
                main_sig =np.real(fftpack.ifft(sig_fft))
                A_[:len(main_sig),2 * (i - 1) + j] = main_sig
        A_ = A_[~np.any(A_ == 0, axis = 1)]  
        return A_
    
    
class velocity():      
    def __init__(self):        
        self.df = df
        self.raw_file = Raw_File

    #速度抽出のmain
    def velocity_and_load_to_csv(self):
        t_ini = 150
        r = 450
        file_num = 1 #1時間
        date = (self.raw_file.split(chr(92))[-1])[:10]

        #名前から時間を持ってくる
        file_0 = str(self.raw_file)
        time_0 = file_0.split("_")[-1]
        min_0 = 0.0001 * (float(time_0[2:8]))
        hour_0 = int(time_0[0:2])
        self.df[:,0] *= -0.208
        self.df[:,1] *= 0.113
        self.df[:,2] *= -0.2437
        self.df[:,3] *= -0.203
        self.df[:,4] *= -0.210
        self.df[:,5] *= -0.214
        self.df[:,6] *= -0.116
        self.df[:,7] *= -0.161
        self.df[:,8] *= -0.278
        self.df[:,9] *= -0.171
        self.df[:,10] *= 0.242
        self.df[:,11] *= -0.207

        B = np.zeros((len(df), 6), dtype = 'float') 
        B[:,0] = self.df[:,0] + self.df[:,2]
        B[:,1] = self.df[:,1] + self.df[:,3]
        B[:,2] = self.df[:,4] + self.df[:,6]
        B[:,3] = self.df[:,5] + self.df[:,7]
        B[:,4] = self.df[:,8] + self.df[:,10]
        B[:,5] = self.df[:,9] + self.df[:,11]
        t1 = self.ExtractData(4, self.df[:,0], self.df[:,2], 1.8)
        t2 = self.ExtractData(4, self.df[:,4], self.df[:,6], 1.8)
        t3 = self.ExtractData(4, self.df[:,8], self.df[:,10],1.8)

        if len(t1) != 0 and len(t2) != 0 and len(t3) != 0:
            TDL1 = self.FindData(t1, t2, 0, 2, 4, 6, df, 10, 1)
            TDL2 = self.FindData(t1, t3, 0, 2, 8, 10, df, 25, 2)
            TDL3 = self.FindData(t2, t3, 4, 6, 8, 10, df, 10, 1)
            TDL2[:,2] += 1
            TDL = np.concatenate([TDL1, TDL2, TDL3])
            TDL_sorted = np.array(sorted(TDL, key=lambda x:(x[0], x[1])))
            TIME = TDL_sorted[:,0]
            DuringTime = TDL_sorted[:,1]
            l = TDL_sorted[:,2]

            #時分の繰り上がり
            T = np.zeros((len(TIME)), dtype = "float")
            MINUTE = (TIME * file_num/ len(df)  - TIME * file_num// len(df) ) * 0.6 + min_0
            HOUR = TIME * file_num// len(df) + hour_0
            for t, (hour, minute) in enumerate(zip(HOUR, MINUTE)):
                while minute >= 0.6:
                    hour += 1
                    minute -= 0.6
                T[t] = hour + minute

            v = l / DuringTime
            n = np.where((v < 0.7) & (v > 0.1))[0]
            n_num = len(n)
            E = np.zeros((n_num,3), dtype = 'float')
            H = np.zeros((6 * n_num, r), dtype = 'float')
            Date = (date.replace('-','')).replace('F_MovAve.csv', '')
            E[:,0] = int(Date)  
            E[:, 1] = T[n]
            E[:, 2] = v[n]
            
            T_ = list(map(int, TIME[n]))
            for count, t in enumerate(T_): 
                    for j in range(3):
                        H[6 * count + 2 * j,:] = B[t - t_ini : t - t_ini + r, 2 * j + 1]
                        H[6 * count + 2 * j + 1,:] = B[t - t_ini : t - t_ini + r, 2 * j]

           
            threshold = 4
            data_count = 0
            while len(E) != data_count:
                hikaku = E[1:, :] - E[:len(E) - 1, :]
                #日付が異なる、もしくは日付同じで時間離れている
                num2 = np.where((hikaku[:,0] != 0) | ((hikaku[:,0] == 0) & (hikaku[:,1] * 1000 > threshold)))[0]
                num2_list = [0] * (len(num2) + 1)
                num2_list[1:] = [i + 1 for i in num2]

                num2 = sorted(num2_list)
                E_new = np.zeros((len(num2), E.shape[1]), dtype = 'float')
                H_new = np.zeros((len(num2) * 6, H.shape[1]), dtype = 'float')

                E_new = E[num2, :]
                for t, p in enumerate(num2):  
                    H_new[t * 6 : (t + 1) * 6,:] = H[p * 6 :(p + 1) * 6, :]

                E = E_new
                H = H_new
                data_count = len(num2)
        else:
            E = np.zeros((1, 3), dtype = 'float')
            H = np.zeros((6, 450), dtype = 'float')
        return E, H  
        
     #しきい値を超えたデータを抽出する関数
    def ExtractData(self, Nnum, df1, df2, threshold):         
        t_ini = 150
        r = 450
        
        b_num_1 = np.where((df1[t_ini + 2 * Nnum:-r - 2 * Nnum] >= threshold) & (df2[t_ini + 2 * Nnum:-r - 2 * Nnum] >= threshold))[0]
        b_num_2 = np.where((df1[t_ini + 2 * Nnum:-r - 2 * Nnum] < - threshold) & (df2[t_ini + 2 * Nnum:-r - 2 * Nnum] < - threshold))[0]

        b = df1 + df2
        a_1 = [i + t_ini + 2 * Nnum for i in b_num_1]
        a_2 = [i + t_ini + 2 * Nnum for i in b_num_2]

        t_1 = [0] * len(a_1)
        t_2 = [0] * len(a_2)
        for count, i in enumerate(a_1):
            x = (b[i - Nnum: i + Nnum])
            index =  i - Nnum + int(np.where(x == max(x))[0][0])
            if index in a_1 and max(x) >= 5.:
                t_1[count] = index

        for count, i in enumerate(a_2):
            x = (b[i - Nnum: i + Nnum])
            index = i - Nnum + int(np.where(x == max(x))[0][0])
            if index in a_2 and max(x) >= 5.:
                t_2[count] =index
        t = list(set(t_1) | set(t_2))
        t = np.array(t)
        t = t[~(t == 0)]
        return t
        
  #いい感じのデータの組を見つけて時間、継続時間、距離を抽出する関数
    def FindData(self, t1, t2, s1, s2, s3, s4, df,threshold_time_max, threshold_time_min):
   
        length1 = df[t1,s1] / (df[t1,s1] + df[t1,s2])
        length2 = df[t2,s4] / (df[t2,s3] + df[t2,s4])

        TDL = np.zeros((len(t1), 3), dtype = 'float')
        count = 0   
        for t1_, l1 in zip(t1, length1): 
            if l1 > 0 and l1 < 1:
                during_time = (-t1_ + t2) / 10
                time_index = np.where((during_time <threshold_time_max) & (during_time > threshold_time_min)                                      & (length2 > 0) & (length2 < 1))[0]
                if len(time_index) != 0:
                    TDL[count, 1] = during_time[time_index][0]
                    TDL[count, 0] = t1_
                    TDL[count, 2] = l1 + length2[time_index][0]
                    count += 1
        return TDL[:count,:]

   

class Analysis():
    def __init__(self):
        self.F = force
        self.index_num = len(force) // 6
    def BF(self):    
        data = np.zeros((self.index_num), dtype = 'float')
        for i in range(self.index_num):
            f = [0] * 3
            for j in range(3):
                f[j] = max(np.sqrt(self.F[6 * i + 2 * j, :] ** 2 + self.F[6 * i + 2 * j + 1, :] ** 2))
            data[i] = max(f)
        return data
    
    def Duration(self):
        t_ini = 0
        t_fin = 450
        num = []
        normal_data_num = []
        during_max = []
        for i in range(self.index_num):
            src = [0] * (t_fin - t_ini)
            temp = [0] * 3
            for j in range(3):
                src = np.sqrt(self.F[6 * i + 2 * j,t_ini:t_ini + t_fin] ** 2 + self.F[6 * i + 2 * j + 1,t_ini:t_ini + t_fin] ** 2)
                dst = [sum(1 for e in it) for _, it in groupby(src, key=lambda x: x >= 3)]
                if len(dst) > 1:
                    if src[0] >= 3:
                        temp[j] = max(dst[::2])

                    elif src[0] < 3:
                        temp[j] = max(dst[1::2])


            during_max.append(max(temp) / 10)
        during_max = np.array(during_max)     
        return during_max


class drawpicture():
    def __init__(self):
        self.date = vel[:,0]
        self.time = vel[:,1]
        self.t = T
        self.v = V
        self.MForce = MF
        self.Duration = D
        self.Ax1 = ax1

    def date_datetime(self):
        dt_f = np.zeros((len(vel)), dtype = 'object')
        for i in range(len(vel)):
            dt_str = str(str(self.date[i])[:4] + '/' + str(self.date[i])[4:6] + '/' + str(self.date[i])[6:8] + " " + str(self.time[i])[:2])
            dt_f[i] = datetime.datetime.strptime(dt_str, "%Y/%m/%d %H")       
        return dt_f

        
if __name__ == '__main__':
    
    T, V, MF, D = [],[],[],[]
    t = []
    DirName = r"C:\Users\Moe HAMADA\Dropbox (LCDLab)\Oono"
    plt.ion()
    fig = plt.figure(figsize = (10, 7))
    fig.suptitle("身体機能変化分析システム", size = 25)
    
    ax1 = fig.add_subplot(2, 2, 1)
    a1 = ax1.scatter(t, V)
    count = 0
    ax1.set_title("昇降速度")
    ax1.set_xlabel("時間 [h]")
    ax1.set_ylabel("速度 [m/s]")
   
    ax2 = fig.add_subplot(2, 2, 2)
    a2 = ax2.scatter(t, MF)
    count = 0
    ax2.set_title("最大負荷")
    ax2.set_xlabel("時間 [h]")
    ax2.set_ylabel("負荷の大きさ [kgf]")

    ax3 = fig.add_subplot(2, 2, 3)
    a3 = ax3.scatter(t, D)
    count = 0
    ax3.set_title("把持継続時間")
    ax3.set_xlabel("時間 [h]")
    ax3.set_ylabel("継続時間 [s]")

    ax4 = fig.add_subplot(2, 2, 4)
    a4_1 = Image.open("pic/couple_fufu_old.png")
    a4_2 = Image.open("pic/unndou.png")  
    plt.tick_params(bottom=False,left=False,right=False,top=False)
    plt.tick_params(labelbottom=False,labelleft=False,labelright=False,labeltop=False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)
    plt.imshow(a4_1)
    
    plt.tight_layout()
    for i in range(1, 51):
    
        da = ArrangeData()

        #最新のファイルを開く
        latest_file_dir = da.get_latest_file_path(DirName, 1)
        latest_file =  da.get_latest_file_path(latest_file_dir, 52 - i)

        Raw_File = latest_file.split(chr(92))[-1]
        #zipファイルを開く
        zf = ZipFile(latest_file)
        b = zf.read(zf.namelist()[0])
        DF = pd.read_csv(BytesIO(b))
        df = np.array(da.fft(DF))
        v = velocity()
        vel, force = v.velocity_and_load_to_csv()
        if vel[0,0] != 0:
            analysis = Analysis()
            maxforce = analysis.BF()
            duration = analysis.Duration()

            for i in range(len(vel)):
                V.append(vel[i,2])
#                 T.append(T_new[0][i])
                t.append(count)
                MF.append(maxforce[i])
                D.append(duration[i])
            TV = np.zeros((len(t),2), dtype = 'object')
            TV[:,0] = t
            TV[:,1] = V
#             print(TV)
            a1.set_offsets(TV)
            ax1.set_xlim(-1, count + 1)
            ax1.set_ylim(0, 1)
            ax1.text(0.99, 0.01, "平均:"  + str(np.mean(V))[:4] + " [m/s]", size=15, backgroundcolor="lightblue",  horizontalalignment='right', transform=ax1.transAxes)
           
            MV = np.zeros((len(t),2), dtype = 'object')
            MV[:,0] = t
            MV[:,1] = MF      
            a2.set_offsets(MV)
            ax2.set_xlim(-1, count + 1)
            ax2.set_ylim(0, max(MV[:,1]) + 5)
            ax2.text(0.99, 0.01, "平均:"  + str(np.mean(MF))[:4] + " [kgf]", size=15, backgroundcolor="lightblue",  horizontalalignment='right', transform=ax2.transAxes)
            
            DV = np.zeros((len(t),2), dtype = 'object')
            DV[:,0] = t
            DV[:,1] = D   
            a3.set_offsets(DV)
            ax3.set_xlim(-1, count + 1)
            ax3.set_ylim(0, max(DV[:,1]) + 5)
            ax3.text(0.99, 0.01, "平均:"  + str(np.mean(D))[:4] + " [s]", size=15, backgroundcolor="lightblue",  horizontalalignment='right', transform=ax3.transAxes)
           
            ax4.cla()          
            if np.mean(V) > 0.35:
                 ax4.text(0.99, 0.01, "その調子です！", size=15, backgroundcolor="lightblue",  horizontalalignment='right', transform=ax4.transAxes)
                 plt.imshow(a4_1)
                
                
            else:
                ax4.text(0.99, 0.01, "運動を推奨します", size=15, backgroundcolor="lightblue",  horizontalalignment='right', transform=ax4.transAxes)
                plt.imshow(a4_2)
                
            fig.canvas.draw_idle()
            plt.pause(0.01)
        else:
            ax1.set_xlim(-1, count + 1)  
            ax2.set_xlim(-1, count + 1)  
            ax3.set_xlim(-1, count + 1)  
            fig.canvas.draw_idle()
            plt.pause(0.01)
        count += 1
    plt.pause(5)


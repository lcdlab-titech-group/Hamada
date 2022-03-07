import serial
from serial.tools import list_ports

class TestOperation():
    
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.baoudrate = baudrate
        self.ser.timeout = None
    
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

    def D_Command(self):
        self.ser.write(b"D001\r") 

    def R_Command(self):
        self.ser.write(b"R001\r")
 
if __name__ == '__main__':
    
    baudrate = 115200 #固定
    Test = TestOperation()
    Ser= Test.select_port()

    #コメントアウトを一つずつ外して結果を確認してください．
#     Test.D_Command() #「D001」とデータが表示されれば正常
#     Test.R_Command() #「!001,01EC,01E9」のようにデータが表示されれば正常
    
    result = Ser.readline()
    result_disp = result.strip().decode('UTF-8')
    print(result_disp)
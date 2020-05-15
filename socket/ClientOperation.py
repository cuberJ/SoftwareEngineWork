import socket
import threading
from threading import Thread
from time import sleep
import os

class UI:
    ClientSocket = None
    ClientSocket2 = None
    WindSpeed = 0  # 表示风速的调整模式，0最低，2最高，一个思路是，change每次+1并模3，实现风速的低中高循环,从而可以少设置一个按键
    Temperature = 18  # 房间的实际温度
    TemperatureSet = 25  # 房间的设定温度
    Cost = 0
    RunTime = 0
    Mode = 1  # 1为制冷模式，0为制热模式
    isRun = 1  # 记录当前是否正在运行客户端,1表示运行
    ConnectSucceed = False
    timeline = ""  # 从后台同步系统实际时间

    def WindSetting(self):  # 修改风速
        # 该模块当前仅设置了传输的模块功能，剩余还需要补充的有：快速连续输入的模式下，需要合并在1s内输入的结果记录在change里，该功能尽量在Menu函数里调用这个函数的时候实现
        self.WindSpeed = (self.WindSpeed + 1) % 3
        print("WindSpeed = ", self.WindSpeed)

    def ModeSetting(self):
        self.Mode = abs(self.Mode - 1)
        print("修改后，模式为：", self.Mode)
        self.TemperatureSet = 25  # 修改模式的时候设定温度回归缺省值

    def TempSetting(self):  # 设定温度
        # 该模块需要补充的与WindInfo一样,发送修改后设定温度
        # 的部分写在Menu的循环里。此外还需要根据当前制热制冷模式设置change的变温范围,写的时候我忘了看PPT，不确定温控范围写的对不对，如果不对，顺带把ModeSetting里的范围一块改了
        oper = input()  # 输入1，升高一度，输入0，减少1度
        if(self.Mode == True) and (self.TemperatureSet < 29) and (oper == "1"):  # 制冷模式升温操作
            self.TemperatureSet += 1
        elif (self.Mode == True) and (self.TemperatureSet > 18) and (oper == "0"): # 制冷模式降温操作
            self.TemperatureSet -= 1
        elif (self.Mode == False) and (self.TemperatureSet < 30) and (oper == "1"):  # 制热模式升温操作
            self.TemperatureSet += 1
        elif (self.Mode == False) and (self.TemperatureSet > 20) and (oper == "0"):  # 制热模式降温操作
            self.TemperatureSet -= 1
        print("修改后，设定温度为：", self.TemperatureSet)

    def TransBuild(self):
        print("当前已经运行时间为", self.RunTime)
        print("当前实际时间为", self.timeline)
        print("当前花费金额为：:", self.Cost)
        print("当前设定温度为:", self.TemperatureSet)
        print("当前实际温度为:", self.Temperature)
        print("当前温控模式为:", self.Mode)

    def RunSet(self):
        self.isRun = abs(self.isRun - 1)
        print("当前机器处于运行状态：", self.isRun)
        return 1

    def Menu(self):  # 操作菜单,修改风速的时候返回1
        print("Please input the operation you want:\n1. Change the wind\n2. Change the temperatue\n3. Change the mode\n")
        choose = input()
        self.ClientSocket2.send(str(choose).encode())
        if choose == "1":
            print("The wind speed now is ", self.WindSpeed)
            self.WindSetting()
            self.ClientSocket2.send(str(self.WindSpeed).encode())
            return 1

        elif choose == "2":
            print("The Temperature in room now is ", self.Temperature)
            print("当前设定温度为：", self.TemperatureSet)
            # 尽量在此处实现1s输入下，合并输入信息的环节，温度和模式同理
            self.TempSetting()
            self.ClientSocket2.send(str(self.TemperatureSet).encode())

        elif choose == "3":
            print("Current mode is", self.Mode)
            self.ModeSetting()
            print(str(self.Mode))
            self.ClientSocket2.send(str(self.Mode).encode())
            self.ClientSocket2.recv(1024)
            self.ClientSocket2.send(str(self.TemperatureSet).encode())

        elif choose == "4":  # 切换开关机模式
            self.RunSet()
            self.ClientSocket2.send(str(self.isRun).encode())

        else:
            print(choose, "the input is wrong ,Please input again...")
        return 0


class Room:  # 房间类，包含UI和sensor类
    ClientSocket = None
    ClientSocket2 = None
    WindSpeed = 0  # 表示风速的调整模式，0最低，2最高，一个思路是，change每次+1并模3，实现风速的低中高循环,从而可以少设置一个按键
    Temperature = 18  # 房间的实际温度
    TemperatureSet = 25  # 房间的设定温度
    Cost = 0
    RunTime = 0
    Mode = 1  # 1为制冷模式，0为制热模式
    isRun = 1  # 记录当前是否正在运行客户端,1表示运行
    ConnectSucceed = False
    timeline = ""  # 从后台同步系统实际时间
    UIInfo = None
    isWindChange = 1

    def __init__(self):
        self.WindSpeedTime = 0  # 当前风速持续的时间
        self.sensor = self.Sensor()
        thread = Thread(target=self.InfoOper)
        thread.setDaemon(True)
        thread.start()

        self.UIInfo = UI()
        self.TransBuild()

    def UIUpdate(self):  # 更新UI信息
        self.RunTime = self.ClientSocket.recv(1024).decode()
        self.RunTime = int(self.RunTime)
        self.ClientSocket.send("#".encode())  # 一收一发，防止运行过快的时候数据被合并
        self.UIInfo.RunTime = self.RunTime

        self.timeline = self.ClientSocket.recv(1024).decode()
        self.ClientSocket.send("#".encode())
        self.UIInfo.timeline = self.timeline

        self.Cost = self.ClientSocket.recv(1024).decode()
        self.Cost = int(self.Cost)
        self.ClientSocket.send("#".encode())
        self.UIInfo.Cost = self.Cost

        self.WindSpeed = self.ClientSocket.recv(1024).decode()
        self.WindSpeed = int(self.WindSpeed)
        self.ClientSocket.send("#".encode())
        self.UIInfo.WindSpeed = self.WindSpeed

        self.TemperatureSet = self.ClientSocket.recv(1024).decode()
        self.TemperatureSet = int(self.TemperatureSet)
        self.ClientSocket.send("#".encode())
        self.UIInfo.TemperatureSet = self.TemperatureSet

        self.Temperature = self.ClientSocket.recv(1024).decode()
        self.Temperature = int(self.Temperature)
        self.ClientSocket.send("#".encode())
        self.UIInfo.Temperature = self.Temperature

        self.Mode = self.ClientSocket.recv(1024).decode()
        self.Mode = int(self.Mode)
        self.ClientSocket.send("#".encode())
        self.UIInfo.Mode = self.Mode
        self.UIInfo.TransBuild()

    def TransBuild(self):
        self.ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('socket---%s' % self.ClientSocket)
        # 链接服务器
        serverAddr = ('localhost', 8848)
        self.ClientSocket.connect(serverAddr)
        print('connect success!')
        print("Welcome to the WindControl System, Here is the main page...")
        self.ConnectSucceed = True

        while True:
            self.UIUpdate()
            print(self.isWindChange)
            if self.isWindChange == 1:
                self.WindSpeedTime = 0
                self.isWindChange = 0
            self.WindSpeedTime += 1
            self.TempChange()

        # 关闭套接字
        self.ClientSocket.close()
        print('close socket!')

    def InfoOper(self):  # 用户界面菜单的操作，和数据传输是独立的两个线程，通过读取，修改类当中的全局变量来使用.初版中因为发送数据的socket写到了UI类的每个子函数里，实在没法单独剔出来，只能不伦不类的写了
        self.ClientSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('socket---%s' % self.ClientSocket2)
        # 链接服务器
        serverAddr = ('localhost', 8849)
        self.ClientSocket2.connect(serverAddr)
        self.UIInfo.ClientSocket2 = self.ClientSocket2
        while True:
            self.isWindChange = self.UIInfo.Menu()

    def TempChange(self):  # 修改房间温度,这里的算法需要你来完成，现在这个是我随手写的
        if (self.WindSpeedTime % 3 == 0) and (self.Mode == 0):
            self.sensor.Temp += 1
        elif (self.WindSpeedTime % 3 == 0) and (self.Mode == 1):
            self.sensor.Temp -= 1
        self.ClientSocket.recv(1024)
        self.ClientSocket.send(str(self.sensor.Temp).encode())

    class Sensor:  # 传感器类，检测温度
        Temp = 26

        def GetTemp(self):
            return self.Temp



test = Room()



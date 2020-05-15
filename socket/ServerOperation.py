import os
import socket
import threading
from threading import Thread
import time
import Monitor
import datetime

Username, Userpassword = None, None
UserActive = []
UserInfoPath = "Info\\"
# 首先看一些总的问题：
# 1. 我在考虑要不要引入某个模块，直接调用Windows的系统时间，这样就不用我们手动去写一个clock了
# 2. 我的登录界面，信息接收模块和计时计费模块是分离的，所以就算是单用户，也是开了多线程
# 3. 细节的实现问题我都在函数里写明了。此外还有一些大型的功能，比如信息接入数据库，多用户的情况下在后台模拟多空调机调度，计费算法都需要你来写了。
# 4. 最终保存的信息需要与数据库进行同步，包括空调计费信息，使用细节以及管理员登录账号和密码，测试阶段可以使用excel存储
# 5. 真实环境的温度模拟
# 溜了溜了，继续肝操作系统的作业……
class ServerData:
    ServerSocket = None
    ServerSocket2 = None
    newServerSocket2 = None
    newServerSocket, destAddr = None, None
    socket_pool = []
    CLOCK = 0  #未来开并发的时候，这里改为数组，然后通过映射对应每个客户端的clock时间
    UserData = []
    WindSpeed = 0 # 表示风速的调整模式
    Temperature = 18  # 房间的实际温度
    TemperatureSet = 25  # 房间的设定温度
    Cost = 0
    RunTime = 0
    Mode = 1  # 1为制冷模式，0为制热模式
    isRun = True  # 记录当前是否正在运行客户端
    SocketSucceed = False
    newServerSocket2 = 0
    newServerSocket = 0
    timeline = ""  # 获取的系统实际时间

    def getCost(self):  # 对外接口，读取当前总花销
        return self.Cost

    def getRunTime(self):
        return self.RunTime

    def getList(self, StartTime, EndTime):  # 对外接口，获得当前为止所有的消费记录,这里需要补充的内容：根据输入的时间获取对应范围内的数据（经理角色的接口）
        return self.UserData

    def RealTem(self):  # 需要补充：模拟真实环境的温度
        pass

    def SocketConnect(self):  # 通讯的主体,也是运行的main函数主要部分
        self.newServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('localhost', 8848)
        self.newServerSocket.bind(address)
        self.newServerSocket.listen(5)
        print('binding succeed!')
        self.newServerSocket, destAddr = self.newServerSocket.accept()
        print(self.newServerSocket)
        self.socket_pool.append(self.newServerSocket)
        self.SocketSucceed = True
    #    下面这几行是历史遗留代码，不用管
    #    thread = Thread(target=AcceptClient, args=(tcpnewServerSocket, Username, Userpassword))
    #    thread.setDaemon(True)
    #    thread.start()
    #    while True:
    #        sleep(1)

        while True:
            self.Time()
            self.newServerSocket.send(str(self.RunTime).encode())
            self.newServerSocket.recv(1024)
            self.newServerSocket.send(self.timeline.encode())
            print("$$$$$$$$$$$$$$$44", self.timeline)
            self.newServerSocket.recv(1024)
            self.newServerSocket.send(str(self.Cost).encode())
            self.newServerSocket.recv(1024)
            self.newServerSocket.send(str(self.WindSpeed).encode())
            self.newServerSocket.recv(1024)
            self.newServerSocket.send(str(self.TemperatureSet).encode())
            self.newServerSocket.recv(1024)
            self.newServerSocket.send(str(self.Temperature).encode())
            self.newServerSocket.recv(1024)
            self.newServerSocket.send(str(self.Mode).encode())
            self.newServerSocket.recv(1024)

            self.newServerSocket.send("isRoomTempChange".encode())
            self.Temperature = self.newServerSocket.recv(1024).decode()
            time.sleep(3)

    def Time(self):  # 这里需要补充：将用时映射为几时几分的具体时间
        self.RunTime += 1
        now = datetime.datetime.now()
        self.timeline = now.strftime("%Y-%m-%d %H:%M:%S")

    def CostRecord(self):  #记录该用户的所有使用记录
        CurrentData = []
        CurrentData.insert(self.CLOCK)
        CurrentData.insert(self.WindSpeed)
        CurrentData.insert(self.Temperature)
        CurrentData.insert(self.TemperatureSet)
        CurrentData.insert(self.Mode)
        CurrentData.insert(self.isRun)
        CurrentData.insert(self.Cost)
        self.UserData.insert(CurrentData)

    def CostCalcu(self):  # 需要补充计费策略
        self.Cost += 1

    def Menu(self):  # 与客户端的Menu对应
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@")
        choose = self.newServerSocket2.recv(1024).decode()
        print("choose:", choose)
        if choose == "1":
            Wind = self.newServerSocket2.recv(1024).decode() # 等待接收风速设定
            print(Wind)
            self.WindSpeed = int(Wind)
            self.WindSpeed = Wind
        elif choose == "2":
            Temp = int(self.newServerSocket2.recv(1024).decode())
            self.TemperatureSet = Temp
        elif choose == "3":
            Mode = self.newServerSocket2.recv(1024).decode()
            self.Mode = int(Mode)
            print(self.Mode)
            self.newServerSocket2.send("#".encode())
            self.TemperatureSet = self.newServerSocket2.recv(1024).decode()
            self.TemperatureSet = int(self.TemperatureSet)
        elif choose == "4":
            self.isRun = self.newServerSocket2.recv(1024).decode()
            self.isRun = int(self.isRun)
        else:
            pass

    def InfoOper(self):  # 与客户端的同名函数对应
        self.ServerSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('localhost', 8849)
        self.ServerSocket2.bind(address)
        self.ServerSocket2.listen(5)
        print('binding succeed!')
        self.newServerSocket2, destAddr = self.ServerSocket2.accept()
        print(self.newServerSocket2)
        self.socket_pool.append(self.newServerSocket2)
        self.SocketSucceed = True
        while True:
            # print("############################")
            self.Menu()


test = ServerData()
Infothread = Thread(target=test.InfoOper)
Infothread.setDaemon(True)
Infothread.start()
MonitorThread = Thread(target=Monitor.FirstUIDeal)
MonitorThread.setDaemon(True)
MonitorThread.start()
test.SocketConnect()
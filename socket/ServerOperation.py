import os
import socket
import threading
from threading import Thread
import time
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
    socket_pool = {}  # 并发的实时信息线程池
    MenuPool = {}  # 并发的按键信息线程池
    CLOCK = {}  # 未来开并发的时候，这里改为数组，然后通过映射对应每个客户端的clock时间
    UserData = []
    WindSpeed = {}  # 表示风速的调整模式
    Temperature = {}  # 房间的实际温度
    TemperatureSet = {}  # 房间的设定温度
    Cost = {}
    RunTime = {}
    Mode = {}  # 1为制冷模式，0为制热模式
    isRun = {}  # 记录当前是否正在运行客户端,1为运行，0为停止（由于布尔变量在socket传输解码过程中会变化，所以先考虑用int）
    SocketSucceed = {}
    timeline = ""  # 获取的系统实际时间
    RoomCount = 0  # 当前已经启动的客户端数目

    def getCost(self):  # 对外接口，读取当前总花销
        return self.Cost

    def getRunTime(self):
        return self.RunTime

    def getList(self, StartTime, EndTime):  # 对外接口，获得当前为止所有的消费记录,这里需要补充的内容：根据输入的时间获取对应范围内的数据（经理角色的接口）
        return self.UserData

    def RealTem(self):  # 需要补充：模拟真实环境的温度
        pass

    def SocketStart(self):  # 通讯的主体,也是运行的main函数主要部分
        ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('localhost', 8848)
        ServerSocket.bind(address)
        ServerSocket.listen(5)
        print('Realtime Socket binding succeed!')
        # 建立完实时信息的通讯线程之后，建立按键的通讯线程
        MenuThread = Thread(target=self.InfoStart)
        MenuThread.setDaemon(True)
        MenuThread.start()
        self.SocketAccept(ServerSocket)
        while True:
            time.sleep(1)

    def SocketAccept(self, ServerSocket):
        while True:
            newServerSocket, destAddr = ServerSocket.accept()
            print(newServerSocket)
            self.socket_pool[newServerSocket] = self.socket_pool.__len__()
            self.SocketSucceed = True
            RoomNumber = self.socket_pool[newServerSocket]
            self.RoomCount += 1
            print("ReadTime 得到的房间号为", RoomNumber)
            # 初始化房间所有部件（风速，温度）的信息
            self.CLOCK[RoomNumber] = 0
            self.WindSpeed[RoomNumber] = 0
            self.Temperature[RoomNumber] = 18
            self.TemperatureSet[RoomNumber] = 26
            self.RunTime[RoomNumber] = 0
            self.Mode[RoomNumber] = 0
            self.isRun[RoomNumber] = 1
            self.Cost[RoomNumber] = 0
            MultiSocket = Thread(target=self.RealTimeInfoOper, args=(newServerSocket, RoomNumber))
            MultiSocket.setDaemon(True)
            MultiSocket.start()

    def RealTimeInfoOper(self, newServerSocket, RoomNumber):
        # 运行实时通讯线程
        while True:
            self.Time(RoomNumber)
            newServerSocket.send(str(self.RunTime[RoomNumber]).encode())
            newServerSocket.recv(1024)
            newServerSocket.send(self.timeline.encode())
            # print(self.timeline)
            newServerSocket.recv(1024)
            newServerSocket.send(str(self.Cost[RoomNumber]).encode())
            newServerSocket.recv(1024)
            newServerSocket.send(str(self.WindSpeed[RoomNumber]).encode())
            newServerSocket.recv(1024)
            newServerSocket.send(str(self.TemperatureSet[RoomNumber]).encode())
            newServerSocket.recv(1024)
            newServerSocket.send(str(self.Temperature[RoomNumber]).encode())
            newServerSocket.recv(1024)
            newServerSocket.send(str(self.Mode[RoomNumber]).encode())
            newServerSocket.recv(1024)

            newServerSocket.send("isRoomTempChange".encode())
            self.Temperature[RoomNumber] = newServerSocket.recv(1024).decode()
            time.sleep(3)

    def Time(self, RoomNumber):  # 这里需要补充：将用时映射为几时几分的具体时间
        self.RunTime[RoomNumber] += 1
        now = datetime.datetime.now()
        self.timeline = now.strftime("%Y-%m-%d %H:%M:%S")

    def CostRecord(self, RoomNumber):  # 记录该用户的所有使用记录
        CurrentData = []
        CurrentData.append(self.CLOCK[RoomNumber])
        CurrentData.append(self.WindSpeed[RoomNumber])
        CurrentData.append(self.Temperature[RoomNumber])
        CurrentData.append(self.TemperatureSet[RoomNumber])
        CurrentData.append(self.Mode[RoomNumber])
        CurrentData.append(self.isRun[RoomNumber])
        CurrentData.append(self.Cost[RoomNumber])
        self.UserData.append(CurrentData)

    def CostCalcu(self, RoomNumber):  # 需要补充计费策略
        self.Cost[RoomNumber] += 1

    def Menu(self, newServerSocket2, RoomNumber):  # 与客户端的Menu对应
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@")
        choose = newServerSocket2.recv(1024).decode()
        print("choose:", choose)
        if choose == "1":
            Wind = newServerSocket2.recv(1024).decode()  # 等待接收风速设定

            self.WindSpeed[RoomNumber] = int(Wind)
            self.WindSpeed[RoomNumber] = Wind
            print(Wind)
            print(self.WindSpeed)
        elif choose == "2":
            Temp = int(newServerSocket2.recv(1024).decode())
            self.TemperatureSet[RoomNumber] = Temp
        elif choose == "3":
            Mode = newServerSocket2.recv(1024).decode()
            self.Mode[RoomNumber] = int(Mode)
            print(self.Mode[RoomNumber])
            newServerSocket2.send("#".encode())
            self.TemperatureSet[RoomNumber] = newServerSocket2.recv(1024).decode()
            self.TemperatureSet[RoomNumber] = int(self.TemperatureSet[RoomNumber])
        elif choose == "4":
            isRun = newServerSocket2.recv(1024).decode()
            self.isRun[RoomNumber] = int(isRun)
        else:
            pass

    def InfoStart(self):  # 按键信息传输的通道建立
        ServerSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('localhost', 8849)
        ServerSocket2.bind(address)
        ServerSocket2.listen(5)
        print('MenuSocket binding succeed!')
        self.InfoAccept(ServerSocket2)


    def InfoAccept(self, ServerSocket2):
        while True:
            newServerSocket2, destAddr = ServerSocket2.accept()
            print(newServerSocket2)
            RoomNumber = self.RoomCount
            print("Menu线程得到的房间号为：", RoomNumber)
            self.MenuPool[newServerSocket2] = RoomNumber
            self.SocketSucceed = True
            MenuThread = Thread(target=self.InfoOper, args=(newServerSocket2, RoomNumber))
            MenuThread.setDaemon(True)
            MenuThread.start()

    def InfoOper(self, newServerSocket2, RoomNumber):
        while True:
            self.Menu(newServerSocket2, RoomNumber)
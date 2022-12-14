import multiprocessing
import logging
from Algo import AlgoServer
from Android import BluetoothMgmt
from Networking import PacketHandler
from Camera import CameraServer
from RCar import RCMgmt
import time
import queue as Queue
from multiprocessing import Manager

manager = Manager()
d = manager.dict()

#Create Process Array
processes = []
#Create multi-thread process queue
process_Queue = multiprocessing.Manager().Queue()

#Create Log for Debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename="DebugLog.txt",level=logging.DEBUG)

# Server Details
ip_Address = '192.168.33.1'
server = AlgoServer.AlgoServer(ip_Address,5000,process_Queue,"ALG", d)

#Create BlueToothManager Thread for Android Connection
bluetoothMgmt = BluetoothMgmt.BluetoothMgmt(1,process_Queue,"AND", d)

#Create RCMgmt Thread for Remote Control Car Connection Via Serial Port
rcCar = RCMgmt.RCMgmt('/dev/ttyUSB0',115200,0,process_Queue,"STM")

#Create Camera Thread for PI Camera Connection, open port 5001
piCamera = CameraServer.CameraServer(ip_Address, 5001 ,process_Queue,"IMG", d);

#Create Packet Handler to identify different services in queue
packetHandler = PacketHandler.PacketHandler()
packetHandler.registerHandler(server)
packetHandler.registerHandler(bluetoothMgmt)
packetHandler.registerHandler(rcCar)
packetHandler.registerHandler(piCamera)

#Adding Services into Process Queue
processes.append(server)
processes.append(bluetoothMgmt)
processes.append(rcCar)
processes.append(piCamera)


while True:
    time.sleep(0.001)
    if(process_Queue.qsize()!=0):
        packetHandler.handle(process_Queue.get())
        process_Queue.task_done()

# Block until all task are done
for t in processes:
    t.join()
print ('All process ended successfully')

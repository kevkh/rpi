import multiprocessing
import logging # for logging purposes
from Algo import AlgoServer
from Android import BluetoothMgmt
from Networking import PacketHandler
from Camera import CameraServer
from RCar import RCMgmt
import time
import queue as Queue

#Create Process Array
processes = []

#Create multi-thread process queue
process_Queue = multiprocessing.Manager().Queue()

#Create Log for Debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename="DebugLog.txt",level=logging.DEBUG)

# Server Details
ip_Address = '192.168.33.1'
server = AlgoServer.AlgoServer(ip_Address,5000,process_Queue,"ALG")

#Create BlueToothManager Thread for Andriod Tablet Connection
bluetoothMgmt = BluetoothMgmt.BluetoothMgmt(1,process_Queue,"AND")

#Create RCMgmt Thread for rcCar Connection Via Serial Por(dev/ttyUSB0), Baud Rate = 115200
rcCar = RCMgmt.RCMgmt('/dev/ttyUSB0',115200,0,process_Queue,"STM")

#Create Camera Thread for PI Camera Connection, port 5001
piCamera = CameraServer.CameraServer(ip_Address, 5001 ,process_Queue,"IMG");

#Create Packet Handler to identify different services in queue
packetHandler = PacketHandler.PacketHandler()
packetHandler.registerHandler(server)
packetHandler.registerHandler(bluetoothMgmt)
#packetHandler.registerHandler(rcCar)  # if not plugged into car, comment tis 
packetHandler.registerHandler(piCamera)


#Adding Services into Process Queue
processes.append(server)
processes.append(bluetoothMgmt)
#processes.append(rcCar)  # if not plugged into car, comment tis 
processes.append(piCamera)

while True:
    time.sleep(0.001)
    if(process_Queue.qsize() != 0):
        packetHandler.handle(process_Queue.get())
        process_Queue.task_done()

# Block until all tasks are completed
for t in processes:
    t.join()
print ('All process ended successfully')
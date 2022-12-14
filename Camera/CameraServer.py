import socket 
import time
import threading
import multiprocessing
import logging
import queue as Queue
import struct
from picamera import PiCamera
import io

class CameraServer(multiprocessing.Process):
    print_lock = threading.Lock()
    handle_q = multiprocessing.Manager().Queue()

    def __init__(self,host,port,job_q,header, db):
        multiprocessing.Process.__init__(self)
        self.port = port
        self.header=header
        self.logger = logging.getLogger(self.__class__.__name__)
        self.host = host
        self.job_q = job_q
        self.c = None 
        self.db = db

        self.daemon=True
        self.start()

    def run(self):
        try:
            #Camera Settings
            self.camera = PiCamera() # OUT OF RESOURCES
            self.camera.rotation = 180
            self.camera.resolution = (640, 480)
            self.camera.start_preview()
            time.sleep(2)

            t2 = threading.Thread(target=self.handleProcessor, args=(0.00001,))
            t2.start()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)

            while True: 
                print("[LOG][IMGPC]","Listening for connection")
                # Create connection with client PC on clientPC.py (Running on another comp)
                self.c, addr = s.accept()
                
                # Lock acquired by client 
                self.print_lock.acquire() 
                print("[LOG][IMGPC]","Connection from:" + str(addr[0]) +":"+ str(addr[1])) 
                self.job_q.put(self.header+":IMG: Camera Processing PC Connected") 
    
                t1 = threading.Thread(target=self.thread_receive,args=(self.c,self.job_q,))
                
                t1.start()
                t1.join()
                
            s.close()
            t2.join()

        finally:
            s.close()
            self.conn.close()

    def getPacketHeader(self):
        return self.header            

    def handleProcessor(self,delay):
        while True:
            if(self.handle_q.qsize()!=0):
                packet = self.handle_q.get()
                print(f"[CameraServer] | packet = {packet}")
                if (packet[:1] == 'x'):   #capture an image once 'x' is detected
                    self.CameraCapture()
                self.handle_q.task_done()
                #self.send_socket(packet)
            time.sleep(delay)

    def CameraCapture(self):
        self.conn = self.c.makefile('wb')
        self.stream = io.BytesIO()
        for frame in self.camera.capture_continuous(self.stream, 'jpeg'):
            self.conn.write(struct.pack('<L', self.stream.tell()))
            self.conn.flush()
            self.stream.seek(0)
            self.conn.write(self.stream.read())
            break
            # self.stream.seek(0)
            # self.stream.truncate()

        self.conn.write(struct.pack('<L', 0))

    def handle(self,packet):
        self.handle_q.put(packet)

    def send_socket(self,message):
        try:
                if(self.c == None):
                    print("[ERR][IMGPC]","Trying to send but no clients connected")
                    # self.job_q.put(self.header+":AND:PC not connected")
                else:
                    self.c.send(message.encode('utf-8'))
        except socket.error as e:
                print(socket.error)
                self.logger.debug(e)
                
        
# Thread Function
    def thread_receive(self,c,job_q):
        while True: 
            try:
                data = c.recv(1024)
                data = data.strip().decode('utf-8')

                if not data: 
                    print('IMG PC Said: Bye')
                    self.print_lock.release()    # lock released on exit 
                    break
                if len(data)>0:
                    
                    print("Img Alphabet Data: " + data)
                    #print("Check AND's job_q.put", job_q.put(self.header+":AND:"+ data)) # Do a print here to check
                    job_q.put(self.header+":AND:"+ data) #send android img data (Uncomment this aft checking above)
                    self.db["IR_IMG_RESULT"] = data   #store img data in db
                    #print(data)
                    print("self.db:", self.db)
                    
                       
            except socket.error as e:
                print(socket.error)
                self.logger.debug(e)
                self.print_lock.release() 
                break
            time.sleep(0.0001)
            
            
        # Close Connection
        c.close() 
      
        



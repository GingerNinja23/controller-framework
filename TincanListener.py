from ipoplib import *
from ControllerModule import ControllerModule

class TincanListener(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='TincanListener',recipient='Logger',\
                                          action='info',data="TincanListener Loaded")
        self.CFxHandle.submitCBT(logCBT)

        self.TincanListenerThread = threading.Thread(target = self.__tincan_listener)
        self.TincanListenerThread.setDaemon(True)
        self.TincanListenerThread.start()

    def processCBT(self,cbt):
        pass

    def timer_method(self):
        pass

    def __tincan_listener(self):
        while(True):
            socks, _, _ = select.select(self.CFxObject.sock_list, [], [], \
                          self.CFxObject.CONFIG["wait_time"])

            if(socks):
                sock_to_read = socks[0]
                data, addr = sock_to_read.recvfrom(self.CFxObject.CONFIG["buf_size"])
                tincanPacket = self.CFxHandle.createCBT(initiator='TincanListener',recipient='TincanDispatcher',\
                                                        action='TINCAN_PKT',data=data)
                self.CFxHandle.submitCBT(tincanPacket)


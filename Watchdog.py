from ipoplib import *
from ControllerModule import ControllerModule

class Watchdog(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='Watchdog',\
                                          recipient='Logger',\
                                          action='info',\
                                          data="Watchdog Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt):

        if(cbt.action == 'STORE_LOCAL_STATE'):
            msg = cbt.data
            self.CFxObject.ipop_state = msg
        else:
            logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                              action='error',\
                                              data="Monitor: Unknown type of CBT "\
                                              "received from: "+cbt.initiator)
            self.CFxHandle.submitCBT(logCBT)


    def timer_method(self):
        do_get_state(self.CFxObject.sock)

    def terminate(self):
        pass



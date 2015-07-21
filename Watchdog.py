from ipoplib import *
from ControllerModule import ControllerModule

class Watchdog(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.ipop_state = None


    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='Watchdog',\
                                          recipient='Logger',\
                                          action='info',\
                                          data="Watchdog Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt):

        if(cbt.action == 'STORE_IPOP_STATE'):
            msg = cbt.data
            self.ipop_state = msg
        elif(cbt.action == 'QUERY_IPOP_STATE'):
            cbt.data = self.ipop_state
            cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator
            # Submit the CBT back to the initiator with data as IPOP state
            self.CFxHandle.submitCBT(cbt)
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



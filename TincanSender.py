from ipoplib import *
from ControllerModule import ControllerModule

class TincanSender(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='TincanSender',recipient='Logger',\
                                          action='info',data="TincanSender Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt):
        pass

    def timer_method(self):
        pass

    def terminate(self):
        pass



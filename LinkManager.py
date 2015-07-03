from ipoplib import *
from ControllerModule import ControllerModule

class LinkManager(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='LinkManager',recipient='Logger',\
                                          action='info',data="LinkManager Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt): 
        

        #logCBT = self.CFxHandle.createCBT(initiator='LinkManager',recipient='Logger',\
        #                                  action='debug',data="LinkManager: Received CBT from "\
        #                                  +cbt.initiator)
        #self.CFxHandle.submitCBT(logCBT)

        if(cbt.action == "CREATE_LINK"):
            # cbt.data is a dict containing all the required values
            uid = cbt.data.get('uid')
            fpr = cbt.data.get('fpr')
            nid = cbt.data.get('nid')
            sec = cbt.data.get('sec')
            cas = cbt.data.get('cas')
            do_create_link(self.CFxObject.sock,uid,fpr,nid,sec,cas)
            logCBT = self.CFxHandle.createCBT(initiator='LinkManager',recipient='Logger',\
                                              action='info',data="Creating Link with peer")
            self.CFxHandle.submitCBT(logCBT)

        elif(cbt.action == "TRIM_LINK"):
            do_trim_link(self.CFxObject.sock,cbt.data) # UID is cbt.data

        else:
            logCBT = self.CFxHandle.createCBT(initiator='LinkManager',recipient='Logger',\
                                              action='warning',data="LinkManager: Invalid CBT received from "\
                                              +cbt.initiator)
            self.CFxHandle.submitCBT(logCBT)

    def timer_method(self):
        pass

    def terminate(self):
        pass



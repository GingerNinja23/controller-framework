import time
import threading
from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class cbtModule(ControllerModule):

    def __init__(self,cfxObject,paramDict):

        self.cfxObject = cfxObject
        self.paramDict = paramDict
        self.pendingCBT = {}

    def processCBT(self): # Main processing loop
        print  "cbtModule Loaded\n"

        time.sleep(2)
        # Send sample CBTs to module A1 and C3
        # Action is to strip the substring "C3" or "A1"
        # from the data by the respective module. But if data starts with "C3"
        # then ModuleA1 can't strip it until ModuleC3 does. So ModuleA1
        # requests ModuleC3 to strip "C3" by issuing a CBT

        cbtA1 = self.cfxObject.createCBT()
        cbtA1.initiator = 'cbtModule'
        cbtA1.recipient = 'ModuleA1'
        cbtA1.action = 'strip'
        cbtA1.data = 'C3A1'

        self.cfxObject.submitCBT(cbtA1)

        cbtC3 = self.cfxObject.createCBT()
        cbtC3.initiator = 'cbtModule'
        cbtC3.recipient = 'ModuleC3'
        cbtC3.action = 'strip'
        cbtC3.data = 'C3A1'

        self.cfxObject.submitCBT(cbtC3)

        # The CM continues to process CBTs until the stop flag
        # is set. Once the stop flag is set, the CM finishes processing
        # the current CBT and then exits

        while(True):
            time.sleep(2)
            cbt = self.cfxObject.getCBT("cbtModule")
            print "cbtModule: CBT received " + str(cbt)+"\n"

            if(cbt.action=='TERMINATE'):
                break
            # Process the CBT here
            # Analyse CBT. If heavy, run it on another thread
            print "cbtModule: Finished Processing the CBT \n"

        print "cbtModule exiting"

    def timer_method(self):
        pass
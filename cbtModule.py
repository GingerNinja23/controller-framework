import time
import random
import threading
from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class cbtModule(ControllerModule):

    def __init__(self,cfxObject,paramDict):

        # A flag to check if the terminate method has been called
        self.stop = threading.Event()

        self.cfxObject = cfxObject
        self.paramDict = paramDict

    def processCBT(self): # Main processing loop
        print  "cbtModule Loaded\n"

        time.sleep(2)
        # Send sample CBTs to module A1 and C3
        # Action is to strip the substring "C3" or "A1"
        # from the data by the respective module. But if data starts with "C3"
        # then ModuleA1 can't strip it until ModuleC3 does. So ModuleA1
        # requests ModuleC3 to strip "C3" by issuing a CBT

        cbtA1 = self.cfxObject.createCBT()
        cbtA1['initiator'] = 'cbtModule'
        cbtA1['recipient'] = 'ModuleC3'
        cbtA1['action'] = 'strip'
        cbtA1['data'] = 'C3A1'

        cbtC3 = {
        'uid': random.randint(1000,9999),
        'initiator':'cbtModule',
        'recipient':'ModuleC3',
        'action':'strip',
        'data':'C3A1'
        }

        self.cfxObject.submitCBT(cbtA1)
        self.cfxObject.submitCBT(cbtC3)

        # The CM continues to process CBTs until the stop flag
        # is set. Once the stop flag is set, the CM finishes processing
        # the current CBT and then exits

        while(not self.stop.is_set()):
            time.sleep(2)
            cbt = self.cfxObject.getCBT("cbtModule")
            print "cbtModule: CBT received " + str(cbt)+"\n"
            # Process the CBT here
            # Analyse CBT. If heavy, run it on another thread
            print "cbtModule: Finished Processing the CBT \n"

        print "cbtModule exiting"

    # This module sets the stop flag, and the CM will no longer
    # call getCBT().
    def terminate(self):
        self.stop.set()





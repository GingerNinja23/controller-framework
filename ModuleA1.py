import time
import threading
from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class ModuleA1(ControllerModule):

    def __init__(self,cfxObject,paramDict):

        self.cfxObject = cfxObject
        self.paramDict = paramDict
        self.pendingCBT = {}

    def processCBT(self): # Main processing loop
        print  "ModuleA1 Loaded\n"

        # The CM continues to process CBTs until the stop flag
        # is set. Once the stop flag is set, the CM finishes processing
        # the current CBT and then exits

        while(True):
            time.sleep(2)
            cbt = self.cfxObject.getCBT("ModuleA1")
            print "Module A1: CBT received " + str(cbt)+"\n"


            if(cbt.action=='TERMINATE'):
                break

            # Process the CBT here
            # Analyse CBT. If heavy, run it on another thread

            # If data starts with C3, ask ModuleC3 to strip "C3" first
            if cbt.data.startswith("C3"):
                newCBT = self.cfxObject.createCBT() 
                newCBT.initiator = "ModuleA1"
                newCBT.recipient = "ModuleC3"
                newCBT.action = 'strip'
                newCBT.data = cbt.data
                
                # Issue CBT to CFx with ModuleC3 as recipient
                self.cfxObject.submitCBT(newCBT)

                self.pendingCBT[cbt.uid] = cbt

                print "ModuleA1: CBT sent to ModuleC3 for processing\n"
            else:
                cbt.data = cbt.data.strip("A1")
                print "ModuleA1: Finished Processing the CBT \n"

        print "ModuleA1 exiting"

    def timer_method(self):
        print "ModuleA1's timer method called"

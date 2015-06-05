import time
import threading
from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class ModuleA1(ControllerModule):

    def __init__(self,cfxObject,paramDict):

        # A flag to check if the terminate method has been called
        self.stop = threading.Event()

        self.cfxObject = cfxObject
        self.paramDict = paramDict

    def processCBT(self): # Main processing loop
        print  "ModuleA1 Loaded\n"

        # The CM continues to process CBTs until the stop flag
        # is set. Once the stop flag is set, the CM finishes processing
        # the current CBT and then exits
        cbt = None
        while(not self.stop.is_set()):
            time.sleep(2)
            try:
                cbt = self.cfxObject.getCBT("ModuleA1")
            except:
                pass
            if(cbt):
                print "Module A1: CBT received " + str(cbt)+"\n"
                # Process the CBT here
                # Analyse CBT. If heavy, run it on another thread

                # If data starts with C3, ask ModuleC3 to strip "C3" first
                if cbt['data'].startswith("C3"): 
                    cbt['initiator'] = "ModuleA1"
                    cbt['recipient'] = "ModuleC3"
                    # Issue CBT to CFx with ModuleC3 as recipient
                    self.cfxObject.submitCBT(cbt)
                    print "ModuleA1: CBT sent to ModuleC3 for processing\n"
                else:
                    cbt['data'] = cbt['data'].strip("A1")
                    print "ModuleA1: Finished Processing the CBT from CFx\n"

        print "ModuleA1 exiting"

    # This module sets the stop flag, and the CM will no longer
    # call getCBT().
    def terminate(self):
        self.stop.set()





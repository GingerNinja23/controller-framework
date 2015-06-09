import time
import threading
from ControllerModule import ControllerModule

# Sample Controller Module 2
# ControllerModule is an abstract class
class ModuleC3(ControllerModule):

    def __init__(self,cfxObject,paramDict):

        self.cfxObject = cfxObject
        self.paramDict = paramDict
        self.pendingCBT = {}

    def processCBT(self): # Main processing loop
        print  "ModuleC3 Loaded\n"

        # The CM continues to process CBTs until the stop flag
        # is set. Once the stop flag is set, the CM finishes processing
        # the current CBT and then exits

        while(True):
            time.sleep(2)
            cbt = self.cfxObject.getCBT("ModuleC3")
            print "Module C3: CBT received " + str(cbt)+"\n"


            if(cbt.action=='TERMINATE'):
                break

            # Process the CBT here
            # Analyse CBT. If heavy, run it on another thread

            # If the request to strip C3 was from another module,
            # strip "C3" and notify it back.
            if(cbt.initiator!='cbtModule' and cbt.initiator!= 'CFx'):

                self.pendingCBT[cbt.uid] = cbt

                cbt.data = cbt.data.strip("C3")
                print "ModuleC3: Finished servicing the request",\
                        "of "+cbt.initiator+". Sending back the CBT\n"

                cbt.recipient = cbt.initiator
                cbt.initiator = "ModuleC3"

                # Submit the CBT to CFx with ModuleA1 as the recipient
                self.cfxObject.submitCBT(cbt)

            else:
                # If CBT was from CFx, just strip "C3"
                cbt.data = cbt.data.strip("C3")
                print "ModuleC3: Finished Processing the CBT \n"

        print "Module C3 exiting"

    def timer_method(self):
        print "ModuleC3's timer method called"
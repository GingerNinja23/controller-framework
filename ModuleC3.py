import time
from ControllerModule import ControllerModule


# Sample Controller Module 2
# ControllerModule is an abstract class
class ModuleC3(ControllerModule):

    def __init__(self,cfxObject,paramDict):
        self.cfxObject = cfxObject
        self.paramDict = paramDict

    def processCBT(self): # Main processing loop
        print  "Module C3 Loaded\n"
        while(True): # Polling approach
            time.sleep(2)
            cbt = self.cfxObject.getCBT("ModuleC3")
            if(cbt):
                print "Module C3: CBT received " + str(cbt)+"\n"
                # Process the CBT here
                # Analyse CBT. If heavy, run it on another thread
    
                # If the request to strip C3 was from another module,
                # strip "C3" and notify it back.
                if(cbt['initiator']!='CFx'):
                    cbt['data'] = cbt['data'].strip("C3")
                    print "ModuleC3: Finished servicing the request",\
                            "of "+cbt['initiator']+". Sending back the CBT\n"

                    cbt['recipient'] = cbt['initiator']
                    cbt['initiator'] = "ModuleC3"

                    # Submit the CBT to CFx with ModuleA1 as the recipient
                    self.cfxObject.submitCBT(cbt)

                else:
                    # If CBT was from CFx, just strip "C3"
                    cbt['data'] = cbt['data'].strip("C3")
                    print "ModuleC3: Finished Processing the CBT from CFx\n"



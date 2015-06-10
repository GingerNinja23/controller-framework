from ControllerModule import ControllerModule

# Sample Controller Module 2
# ControllerModule is an abstract class
class ModuleC3(ControllerModule):

    def __init__(self,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}

    def initialize(self):
        
        print  "ModuleC3 Loaded\n"

    def processCBT(self,cbt): 

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
            self.CFxHandle.submitCBT(cbt)

        else:
            # If CBT was from CFx, just strip "C3"
            cbt.data = cbt.data.strip("C3")
            print "ModuleC3: Finished Processing the CBT \n"

    def timer_method(self):
        print "ModuleC3's timer method called"


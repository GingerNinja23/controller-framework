from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class ModuleA1(ControllerModule):

    def __init__(self,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}

    def initialize(self):
        
        print  "ModuleA1 Loaded\n"

    def processCBT(self,cbt): 
        
        # Process the CBT here
        # Analyse CBT. If heavy, run it on another thread

        # If data starts with C3, ask ModuleC3 to strip "C3" first
        if cbt.data.startswith("C3"):
            newCBT = self.CFxHandle.createCBT() 
            newCBT.initiator = "ModuleA1"
            newCBT.recipient = "ModuleC3"
            newCBT.action = 'strip'
            newCBT.data = cbt.data
            
            # Issue CBT to CFx with ModuleC3 as recipient
            self.CFxHandle.submitCBT(newCBT)

            self.pendingCBT[cbt.uid] = cbt

            print "ModuleA1: CBT sent to ModuleC3 for processing\n"

        else:
            cbt.data = cbt.data.strip("A1")
            print "ModuleA1: Finished Processing the CBT \n"

    def timer_method(self):
        print "ModuleA1's timer method called"


from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class cbtModule(ControllerModule):

    def __init__(self,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}

    def initialize(self):

        print  "cbtModule Loaded\n"

        # Send sample CBTs to module A1 and C3
        # Action is to strip the substring "C3" or "A1"
        # from the data by the respective module. But if data starts with "C3"
        # then ModuleA1 can't strip it until ModuleC3 does. So ModuleA1
        # requests ModuleC3 to strip "C3" by issuing a CBT

        cbtA1 = self.CFxHandle.createCBT()
        cbtA1.initiator = 'cbtModule'
        cbtA1.recipient = 'ModuleA1'
        cbtA1.action = 'strip'
        cbtA1.data = 'C3A1'

        self.CFxHandle.submitCBT(cbtA1)

        cbtC3 = self.CFxHandle.createCBT()
        cbtC3.initiator = 'cbtModule'
        cbtC3.recipient = 'ModuleC3'
        cbtC3.action = 'strip'
        cbtC3.data = 'C3A1'

        self.CFxHandle.submitCBT(cbtC3)

    def processCBT(self,cbt): 

        # Process the CBT here
        # Analyse CBT. If heavy, run it on another thread
        print "cbtModule: Finished Processing the CBT \n"

    def timer_method(self):
        pass


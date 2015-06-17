from ControllerModule import ControllerModule

# Sample Controller Module 1
# ControllerModule is an abstract class
class cbtModule(ControllerModule):

    def __init__(self,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.cbtTestCases = [] # List for test CBTs

    def initialize(self):

        print  "cbtModule Loaded\n"

        # Send sample CBTs to the controller modules
        # Action is to follow the path given in the data.
        # Last element of the list represents the current location in the path

        cbtA1 = self.CFxHandle.createCBT('cbtModule','ModuleA1','path',['A1',0])
        self.cbtTestCases.append(cbtA1)

        # cbtB2 = self.CFxHandle.createCBT('cbtModule','ModuleB2','path',['B2',0])
        #self.cbtTestCases.append(cbtB2)

        # cbtC3 = self.CFxHandle.createCBT('cbtModule','ModuleC3','path',['C3',0])
        #self.cbtTestCases.append(cbtC3)

        cbtA1C3 = self.CFxHandle.createCBT('cbtModule','ModuleA1','path',['A1','C3',0])
        self.cbtTestCases.append(cbtA1C3)

        cbtC3B2 = self.CFxHandle.createCBT('cbtModule','ModuleC3','path',['C3','B2',0])
        self.cbtTestCases.append(cbtC3B2)

        #cbtA1B2C3 = self.CFxHandle.createCBT('cbtModule','ModuleA1','path',['A1','B2','C3',0])
        #self.cbtTestCases.append(cbtC3B2)

        #cbtA1B2A1 = self.CFxHandle.createCBT('cbtModule','ModuleA1','path',['A1','B2','A1',0])
        #self.cbtTestCases.append(cbtA1B2A1)

    def processCBT(self,cbt): 

        # Process the CBT here
        # Analyse CBT. If heavy, run it on another thread
        #print "cbtModule: Finished Processing the CBT \n"
        pass

    def timer_method(self):

        print "\n---------------------------------------"
        print "CFxModule Timer called. Submitting CBT\n"
        if(self.cbtTestCases):
            cbt = self.cbtTestCases.pop(0)
            print "Recipient: "+cbt.recipient+", Data: "+str(cbt.data)+", Action: "+cbt.action+"\n"
            self.CFxHandle.submitCBT(cbt)
        else:
            print "No more test cases left"


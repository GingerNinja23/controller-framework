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
        print "ModuleC3: Received CBT from "+cbt.initiator

        if cbt.uid in self.pendingCBT:

            if (cbt.data[-1] == 0):
                print "Module C3: Finished processing the CBT"
            else:
                # Tie back to the old CBT
                pass

        else:
            
            if(len(cbt.data)==2):
                print "Module C3: Finished processing the CBT"

            elif(len(cbt.data)==cbt.data[-1]+2 and len(cbt.data) != 2):
                cbt.data[-1] -= 1
                cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator
                self.CFxHandle.submitCBT(cbt)
                print "ModuleC3 : Finished servicing request of "+cbt.recipient+". Sending back the CBT\n"

            else:
                cbt.data[-1] += 1 
                
                newCBT = self.CFxHandle.createCBT("ModuleC3","Module"+cbt.data[cbt.data[-1]],'path',cbt.data) 
                
                # Issue CBT to CFx with the next Module in the list as recipient
                self.CFxHandle.submitCBT(newCBT)

                self.pendingCBT[newCBT.uid] = newCBT

                print "ModuleC3: CBT sent to Module"+cbt.data[cbt.data[-1]]+" for processing\n"

    def timer_method(self):
        print "ModuleC3's timer method called"


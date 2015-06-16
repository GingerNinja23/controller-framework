from ControllerModule import ControllerModule

# Sample Controller Module 2
# ControllerModule is an abstract class
class ModuleB2(ControllerModule):

    def __init__(self,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}

    def initialize(self):
        
        print  "ModuleB2 Loaded\n"

    def processCBT(self,cbt): 
        
        # Process the CBT here
        # Analyse CBT. If heavy, run it on another thread
        print "ModuleB2: Received CBT from "+cbt.initiator

        # Check if the CBT is a new one or response to a
        # submitted CBT
        if cbt.uid in self.pendingCBT:

            if (cbt.data[-1] == 0):
                print "Module B2: Finished processing the CBT"
            else:
                # Tie back to the old CBT
                pass

        else:
            
            # Check if only one module is there in the path
            if(len(cbt.data)==2):
                print "Module B2: Finished processing the CBT"

            # If the pointer points to last CBT, send the CBT back
            # to the source 
            elif(len(cbt.data)==cbt.data[-1]+2 and len(cbt.data) != 2):
                cbt.data[-1] -= 1
                cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator
                self.CFxHandle.submitCBT(cbt)
                print "ModuleB2 : Finished servicing request of "+cbt.recipient+\
                ". Sending back the CBT\n"

            # If pointer does not point to last CBT, submit a CBT to the 
            # module next in the path list
            else:
                cbt.data[-1] += 1 
                
                newCBT = self.CFxHandle.createCBT("ModuleB2","Module"+cbt.data[cbt.data[-1]],\
                    'path',cbt.data) 
                
                # Issue CBT to CFx with the next Module in the list as recipient
                self.CFxHandle.submitCBT(newCBT)

                self.pendingCBT[newCBT.uid] = newCBT

                print "ModuleB2: CBT sent to Module"+cbt.data[cbt.data[-1]]+" for processing\n"

    def timer_method(self):
        print "ModuleB2's timer method called"


#!/usr/bin/env python
import json
import Queue
from threading import Thread
import importlib
import time
import random


class CFX(object):

    def __init__(self):

        with open('config.json') as data_file:    
            self.json_data = json.load(data_file) # Read config.json
            self.cfxParameterDict = self.json_data['CFx'] # CFx parameters retrieved from config.json

            self.queueDict = {} # A dict of all the queues. Module name is the key and the value is the queue
            self.pendingDict = {} # A dict of all the pending CBT dictionaries
            self.moduleInstances = {} # A dict containing the references to all modules
            # All the above dicts have the module name as the key

    def getCBT(self,moduleName):

        try:
            cbt = self.queueDict[moduleName].get(False) # Get CBT from the Queue. Exception is raised if queue is empty
            self.addToPendingDict(cbt,moduleName) # Add the CBT to the pendingCBT dict of the module
            return cbt

        except Queue.Empty: # return None if the queue is empty
            return None

    def submitCBT(self,CBT):
        recipient = CBT['recipient'] # Check the recipient of the CBT
        self.queueDict[recipient].put(CBT) # Put the CBT in appropriate queue

    def addToPendingDict(self,CBT,moduleName):
        self.pendingDict[moduleName][CBT['uid']] = CBT # Put the CBT in pendingCBT dict with UID of the CBT as the key.

    def mainFunction(self,):
        print "CFx Loaded. Initializing Modules\n"
        for key in self.json_data: # Iterating through the modules mentioned in config.json
            if (key != 'CFx'):
                #print key
                self.queueDict[key] = Queue.Queue() # Create housekeeping structures
                self.pendingDict[key] = {} # Create housekeeping structures

                module = importlib.import_module(key) # Dynamically importing the modules
                class_ = getattr(module,key) # Get the class with name key from module
                instance = class_(self,self.json_data[key]) # Instantiate the class, with CFx object reference and configuration parameters
                self.moduleInstances[key] = instance

                # Sample CBT. Action is to strip the substring "C3" or "A1" from the data by the respective module. 
                # But if data starts with "C3" then ModuleA1 can't strip it until ModuleC3 does. So ModuleA1
                # requests ModuleC3 to strip "C3" by issuing a CBT
                cbt = {'uid': random.randint(1000,9999),'initiator':'CFx','recipient':key,'action':'strip','data':'C3A1'}

                self.queueDict[key].put(cbt) # Queue the CBT in appropriate queue
                thread = Thread(target = self.thread_function,args=(instance,)) # Run the main processing function of the module on a different thread.
                thread.start()

    def thread_function(self,instance):
        instance.processCBT() # Run the main processing function of the module on a different thread.

def main():
    CFx = CFX()
    CFx.mainFunction()

if __name__ == "__main__":
    main()
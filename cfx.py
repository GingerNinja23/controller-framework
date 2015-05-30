#!/usr/bin/env python
import json
import Queue
import time
import random
import importlib
from threading import Thread


class CFX(object):

    def __init__(self):

        with open('config.json') as data_file:    
            self.json_data = json.load(data_file) # Read config.json

            # CFx parameters retrieved from config.json
            self.cfxParameterDict = self.json_data['CFx']

            # A dict of all the queues. Module name is the key
            # and the value is the queue
            self.queueDict = {} 
            # A dict of all the pending CBT dictionaries
            self.pendingDict = {}
            # A dict containing the references to all modules
            self.moduleInstances = {} 
            # All the above dicts have the module name as the key

    def getCBT(self,moduleName):

        try:
            # Get CBT from the Queue. Exception is raised if queue is empty
            cbt = self.queueDict[moduleName].get(False)

            # Add the CBT to the pendingCBT dict of the module
            self.addToPendingDict(cbt,moduleName)

            return cbt

        except Queue.Empty: # return None if the queue is empty
            return None

    def submitCBT(self,CBT):

        # Check the recipient of the CBT
        recipient = CBT['recipient']

        # Put the CBT in appropriate queue
        self.queueDict[recipient].put(CBT)

    def addToPendingDict(self,CBT,moduleName):

        # Put the CBT in pendingCBT dict with UID of the CBT as the key.
        self.pendingDict[moduleName][CBT['uid']] = CBT

    def mainFunction(self,):

        print "CFx Loaded. Initializing Modules\n"

        # Iterating through the modules mentioned in config.json
        for key in self.json_data:
            if (key != 'CFx'):
                self.queueDict[key] = Queue.Queue() # Create housekeeping structures
                self.pendingDict[key] = {} # Create housekeeping structures

                module = importlib.import_module(key) # Dynamically importing the modules
                class_ = getattr(module,key) # Get the class with name key from module

                # Instantiate the class, with CFx object reference and configuration parameters
                instance = class_(self,self.json_data[key])
                self.moduleInstances[key] = instance

                # Sample CBT. Action is to strip the substring "C3" or "A1"
                # from the data by the respective module. But if data starts with "C3"
                # then ModuleA1 can't strip it until ModuleC3 does. So ModuleA1
                # requests ModuleC3 to strip "C3" by issuing a CBT
                cbt = {
                        'uid': random.randint(1000,9999),
                        'initiator':'CFx',
                        'recipient':key,
                        'action':'strip',
                        'data':'C3A1'
                }

                self.queueDict[key].put(cbt) # Queue the CBT in appropriate queue

                # Run the main processing function of the module on a different thread.
                thread = Thread(target = self.thread_function,args=(instance,)) 
                thread.start()

    def thread_function(self,instance):
        # Run the main processing function of the module on a different thread.
        instance.processCBT()


def main():
    CFx = CFX()
    CFx.mainFunction()

if __name__ == "__main__":
    main()



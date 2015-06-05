#!/usr/bin/env python
import sys
import json
import Queue
import time
import random
import signal
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

            self.threadList = []

            self.__initialize()

    def getCBT(self,moduleName):

        # Get CBT from the Queue. Exception is raised if queue is empty

        try:
            cbt = self.queueDict[moduleName].get(False)
            
            # Add the CBT to the pendingCBT dict of the module
            self.__addToPendingDict(cbt,moduleName)

            return cbt

        except:
            return None


    def submitCBT(self,CBT):

        # Check the recipient of the CBT
        recipient = CBT['recipient']

        # Put the CBT in appropriate queue
        self.queueDict[recipient].put(CBT)

    def __addToPendingDict(self,CBT,moduleName):

        # This is a private method, and cannot be called by the CMs

        # Put the CBT in pendingCBT dict with UID of the CBT as the key.
        self.pendingDict[moduleName][CBT['uid']] = CBT

    def __initialize(self,):

        # This is a private method, and cannot be called by the CMs

        try:
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
                    thread = Thread(target = self.__thread_function,args=(instance,))
                    thread.setDaemon(True)
                    self.threadList.append(thread)
                    thread.start()

            # This works on Linux Only
            #for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]: 
                #signal.signal(sig, self.__handler)


            # Prevent main thread from exiting.
            while True:
                time.sleep(1)

        # Gracefully terminate the controller when SIGINT is raised
        # or sys.exit() is called
        except KeyboardInterrupt,SystemExit:
            print 'Shutdown signal received, terminating the controller'
            self.__terminate()
            sys.exit(0)

    def __thread_function(self,instance):

        # This is a private method, and cannot be called by the CMs

        # Run the main processing function of the module on a different thread.
        instance.processCBT()

    def __handler(signum = None, frame = None):

        # This is a private method, and cannot be called by the CMs

        print 'Signal handler called with signal', signum
        self.__terminate()
        # Exit the main thread
        sys.exit(0)

    def __terminate(self):
        
        # This is a private method, and cannot be called by the CMs
        # This method calls the terminate methods of all the CMs and 
        # waits for all the threads to exit.
        for key in self.moduleInstances:
            self.moduleInstances[key].terminate()
        for thread in self.threadList:
            thread.join()

def main():
    CFx = CFX()

if __name__ == "__main__":
    main()




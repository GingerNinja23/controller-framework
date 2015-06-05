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

    def getCBT(self,moduleName):

        # Get CBT from the Queue. Exception is raised if queue is empty
        cbt = self.queueDict[moduleName].get()

        return cbt

    def submitCBT(self,CBT):

        # Check the recipient of the CBT
        recipient = CBT['recipient']

        # Put the CBT in appropriate queue
        self.queueDict[recipient].put(CBT)

    def addToPendingDict(self,CBT,moduleName):

        # Put the CBT in pendingCBT dict with UID of the CBT as the key.
        self.pendingDict[moduleName][CBT['uid']] = CBT

    def initialize(self,):

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


                # Run the main processing function of the module on a different thread.
                thread = Thread(target = self.__thread_function,args=(instance,))
                thread.setDaemon(True)
                self.threadList.append(thread)
                thread.start()

    def __thread_function(self,instance):

        # This is a private method, and cannot be called by the CMs

        # Run the main processing function of the module on a different thread.
        instance.processCBT()

    def waitForShutdownEvent(self):

        # This works on Linux Only
        #for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]: 
        #signal.signal(sig, self.__handler)

        while(True):
            try:
                time.sleep(1)
            except KeyboardInterrupt,SystemExit:
                print 'Shutdown signal received, terminating the controller\n'
                break

    def terminate(self):

        # This method calls the terminate methods of all the CMs and 
        # waits for all the threads to exit.
        for key in self.moduleInstances:
            self.moduleInstances[key].terminate()

        for key in self.queueDict:
            
            # Create a special terminate CBT to terminate the CMs
            terminateCBT = self.createCBT()
            terminateCBT['initiator'] = 'CFx'
            terminateCBT['recipient'] = key
            terminateCBT['action'] = 'TERMINATE'
            self.queueDict[key].put(terminateCBT)

        for thread in self.threadList:
            thread.join()
        sys.exit(0)

    def __handler(signum = None, frame = None):

        # This is a private method, and cannot be called by the CMs

        print 'Signal handler called with signal', signum
        self.terminate()

    def createCBT(self):
        CBT = {
                'uid': random.randint(1000,9999),
                'initiator':'',
                'recipient':'',
                'action':'',
                'data':''
        }
        return CBT


def main():
    CFx = CFX()
    CFx.initialize()
    CFx.waitForShutdownEvent()
    CFx.terminate()

if __name__ == "__main__":
    main()




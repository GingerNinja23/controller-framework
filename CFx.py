#!/usr/bin/env python
import sys
import json
import signal
import threading
import importlib
from CBT import CBT as _CBT
from CFxHandle import CFxHandle


class CFX(object):

    def __init__(self):

        with open('config.json') as data_file:
            self.json_data = json.load(data_file) # Read config.json

            # CFx parameters retrieved from config.json
            self.cfxParameterDict = self.json_data['CFx']

            # A dict containing the references to CFxHandles of all CMs
            # Key is the module name 
            self.CFxHandleDict = {} 

            # This list contains all the threads that the CFx needs 
            # to wait for (by calling join() on them) before exiting
            self.joinThreadList = []

            # All the threads that are to be started by the CFx
            self.startThreadList = []

    def submitCBT(self,CBT):

        # Check the recipient of the CBT
        recipient = CBT.recipient

        # Put the CBT in appropriate queue
        self.CFxHandleDict[recipient].CMQueue.put(CBT)

    def initialize(self,):

        print "CFx Loaded. Initializing Modules\n"

        # Iterating through the modules mentioned in config.json
        for key in self.json_data:
            if (key != 'CFx'):

                module = importlib.import_module(key) # Dynamically importing the modules
                class_ = getattr(module,key) # Get the class with name key from module

                _CFxHandle = CFxHandle(self) # Create a CFxHandle object for each module

                # Instantiate the class, with CFxHandle reference and configuration parameters
                instance = class_(_CFxHandle,self.json_data[key])

                _CFxHandle.CMInstance = instance
                _CFxHandle.CMConfig = self.json_data[key]

                # Store the CFxHandle object references in the dict with module name as the key
                self.CFxHandleDict[key] = _CFxHandle

        # Intialize all the CFxHandles which in turn initializes the CMs
        for key in self.CFxHandleDict:
            self.CFxHandleDict[key].initialize()

        # Start all the worker threads
        for thread in self.startThreadList:
            thread.start()

    def waitForShutdownEvent(self):

        # This works on Linux Only
        #for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]: 
        #signal.signal(sig, self.__handler)

        # Wait for a KeyboardInterrupt or the exception caused by sys.exit()
        event = threading.Event()
        while(True):
            try:
                event.wait(0.1)
            except KeyboardInterrupt,SystemExit:
                print 'Shutdown signal received, terminating the controller\n'
                break

    def terminate(self):

        for key in self.CFxHandleDict:

            # Create a special terminate CBT to terminate all the CMs
            terminateCBT = self.createCBT()
            terminateCBT.initiator = 'CFx'
            terminateCBT.recipient = key
            terminateCBT.action = 'TERMINATE'

            # Clear all the queues and put the terminate CBT in all the queues
            self.CFxHandleDict[key].CMQueue.queue.clear()

            self.submitCBT(terminateCBT)

        # Wait for the threads to process their current CBTs
        for thread in self.joinThreadList:
            thread.join()

        sys.exit(0)

    def __handler(signum = None, frame = None):

        # This is a private method, and cannot be called by the CMs

        print 'Signal handler called with signal', signum
        self.terminate()

    def createCBT(self):

        # Create and return an empty CBT. The variables of the CBT 
        # will be assigned by the CM
        cbt = _CBT()
        return cbt

    def freeCBT(self):

        # Deallocate the CBT here
        # Python automatic garbage collector handles it anyway
        pass


def main():
    CFx = CFX()
    CFx.initialize()
    CFx.waitForShutdownEvent()
    CFx.terminate()

if __name__ == "__main__":
    main()


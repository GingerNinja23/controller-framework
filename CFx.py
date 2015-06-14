#!/usr/bin/env python
import os
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

        for handle in self.CFxHandleDict:
            # Intialize all the CFxHandles which in turn initialize the CMs
            self.CFxHandleDict[handle].initialize()

        # Start all the worker threads
        for handle in self.CFxHandleDict:
            self.CFxHandleDict[handle].CMThread.start()
            if(self.CFxHandleDict[handle].timer_thread):
                self.CFxHandleDict[handle].timer_thread.start()

    def waitForShutdownEvent(self):

        self.event = threading.Event()

        # Since signal.pause() is not avaialble on windows, use event.wait()
        # with a timeout to catch KeyboardInterrupt. Without timeout, it's 
        # not possible to catch KeyboardInterrupt because event.wait() is 
        # a blocking call without timeout. The if condition checks if the os
        # is windows.
        if(os.name == 'nt'):

            while(True):
                try:
                    self.event.wait(999999)
                except KeyboardInterrupt,SystemExit:
                    break

        else:
            
            for sig in [signal.SIGINT]: 
                signal.signal(sig, self.__handler)
            signal.pause()

    def terminate(self):

        for key in self.CFxHandleDict:

            # Create a special terminate CBT to terminate all the CMs
            terminateCBT = self.createCBT('CFx',key,'TERMINATE','')

            # Clear all the queues and put the terminate CBT in all the queues
            self.CFxHandleDict[key].CMQueue.queue.clear()

            self.submitCBT(terminateCBT)

        # Wait for the threads to process their current CBTs
        for handle in self.CFxHandleDict:
            if(self.CFxHandleDict[handle].joinEnabled):
                self.CFxHandleDict[handle].CMThread.join()

        sys.exit(0)

    def __handler(self,signum = None, frame = None):

        # This is a private method, and cannot be called by the CMs

        print 'Signal handler called with signal', signum
        

    def createCBT(self,initiator='',recipient='',action='',data=''):

        # Create and return an empty CBT. The variables of the CBT 
        # will be assigned by the CM
        cbt = _CBT(initiator,recipient,action,data)
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


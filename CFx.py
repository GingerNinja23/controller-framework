#!/usr/bin/env python
import sys
import json
import Queue
import time
import signal
import importlib
from CBT import CBT as _CBT
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

            # This list contains all the threads that the CFx needs 
            # to wait for (by calling join() on them) before exiting
            self.threadList = []

    def getCBT(self,moduleName):

        # Get CBT from the Queue. This is a blocking call and will block the
        # calling thread until an item is put into the corresponding Queue
        cbt = self.queueDict[moduleName].get()

        return cbt

    def submitCBT(self,CBT):

        # Check the recipient of the CBT
        recipient = CBT.recipient

        # Put the CBT in appropriate queue
        self.queueDict[recipient].put(CBT)

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
                thread = Thread(target = self.__worker,args=(instance,))
                thread.setDaemon(True)

                # Read config.json and add the threads to the list accordingly
                if(self.json_data[key]['CBTterminate'] == 'False'):
                    self.threadList.append(thread)

                thread.start()

                interval = self.json_data[key]['timer_interval']

                if(interval != "NONE"):
                    timer_enabled = True

                    try:
                        interval = int(interval)
                        
                    except:

                        print "Invalid timer configuration for "+key+\
                        ". Timer is disabled for this module"
                        timer_enabled = False

                else:
                    timer_enabled = False

                if(timer_enabled):

                    timer_thread = Thread(target = self.__timer_worker,args=(instance,interval,))
                    timer_thread.setDaemon(True)
                    timer_thread.start()

    def __worker(self,instance):

        # This is a private method, and cannot be called by the CMs

        # Run the main processing function of the module on a different thread.
        instance.processCBT()

    def __timer_worker(self,instance,interval):

        # Call the timer_method of CMs at a given freqeuency

        while(True):
            time.sleep(interval)
            instance.timer_method()


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

        for key in self.queueDict:

            # Create a special terminate CBT to terminate all the CMs
            terminateCBT = self.createCBT()
            terminateCBT.initiator = 'CFx'
            terminateCBT.recipient = key
            terminateCBT.action = 'TERMINATE'

            # Clear all the queues and put the terminate CBT in all the queues
            self.queueDict[key].queue.clear()

            self.queueDict[key].put(terminateCBT)

        for thread in self.threadList:
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


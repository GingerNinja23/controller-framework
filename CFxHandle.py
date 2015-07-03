import Queue
import logging
import threading

class CFxHandle(object):

    def __init__(self,CFxObject):

        self.CMQueue = Queue.Queue() # For CBTs
        self.CMInstance = None # CFx assigns value to this variable
        self.CMThread = None # CM worker thread
        self.CMConfig = None # Config of the CM from config.json
        self.__CFxObject = CFxObject # CFx object reference
        self.joinEnabled = False
        self.timer_thread = None

    def __getCBT(self):

        cbt = self.CMQueue.get() # Blocking call
        return cbt

    def submitCBT(self,cbt):

        # Submit to CFx which then submits it to the appropriate CM
        self.__CFxObject.submitCBT(cbt) 

    def createCBT(self,initiator='',recipient='',action='',data=''):

        # Create and return an empty CBT. The variables of the CBT 
        # will be assigned by the CM
        cbt = self.__CFxObject.createCBT(initiator,recipient,action,data)
        return cbt

    def freeCBT(self):

        # Deallocate the CBT here
        # Python automatic garbage collector handles it anyway
        pass

    def initialize(self):

        # Intialize CM first
        self.CMInstance.initialize()

        # Create worker thread and add to startThreadList
        # CFx will then start all the threads
        self.CMThread = threading.Thread(target = self.__worker)
        self.CMThread.setDaemon(True)

        # Check whether CM requires join() or not
        if(self.CMConfig['joinEnabled'] == 'True'):
            self.joinEnabled = True

        # Check if the CMConfig has timer_interval specified
        # If not then assume timer functionality not required
        try:
            interval = self.CMConfig['timer_interval']
        except:
            interval = "NA"


        if(interval != "NA"):
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

            # Create timer worker thread
            self.timer_thread = threading.Thread(target = self.__timer_worker,\
                                                 args=(interval,))
            self.timer_thread.setDaemon(True)

    def __worker(self):
        
        # Get CBT from local queue, and call processCBT() which
        # is responsible for processing one CBT given as a parameter
        while(True):

            cbt = self.__getCBT()

            # Break the loop if special terminate CBT received
            if(cbt.action == 'TERMINATE'):
                module_name = self.CMInstance.__class__.__name__
                logging.info(module_name+" exiting")
                if(self.timer_thread):
                    self.timer_thread.stop()
                self.CMInstance.terminate()
                break
            else:
                self.CMInstance.processCBT(cbt)

    def __timer_worker(self,interval):

        # Call the timer_method of CMs at a given freqeuency
        event = threading.Event()

        while(True):
            event.wait(interval)
            self.CMInstance.timer_method()


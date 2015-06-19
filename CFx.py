#!/usr/bin/env python
import os
import sys
import json
import signal
import threading
import importlib
import logging
from ipoplib import *
from CBT import CBT as _CBT
from CFxHandle import CFxHandle

class CFX(UdpServer):

    def __init__(self):

        
        with open('config.json') as data_file:
            self.json_data = json.load(data_file) # Read config.json

        # A dict containing the references to CFxHandles of all CMs
        # Key is the module name 
        self.CFxHandleDict = {} 
        self.idle_peers = {}
        self.user = CONFIG["xmpp_username"]
        self.password = CONFIG["xmpp_password"] 
        self.host = CONFIG["xmpp_host"] 
        self.ip4 = CONFIG["ip4"]
        self.uid = gen_uid(self.ip4) # SHA-1 hash
        self.vpn_type = "GroupVPN"

        self.uid_ip_table = {}
        parts = CONFIG["ip4"].split(".")
        ip_prefix = parts[0] + "." + parts[1] + "."
        # Populating the uid_ip_table with all the IPv4 addresses
        # and the corresponding UIDs in the /16 subnet
        for i in range(0, 255):
            for j in range(0, 255):
                ip = ip_prefix + str(i) + "." + str(j)
                uid = gen_uid(ip)
                self.uid_ip_table[uid] = ip

        UdpServer.__init__(self, self.user, self.password, self.host, self.ip4)


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
                instance = class_(self,_CFxHandle,self.json_data[key])

                _CFxHandle.CMInstance = instance
                _CFxHandle.CMConfig = self.json_data[key]

                # Store the CFxHandle object references in the dict with module name as the key
                self.CFxHandleDict[key] = _CFxHandle

                # Intialize all the CFxHandles which in turn initialize the CMs    
                _CFxHandle.initialize()

        # Set to false for now
        # if self.CONFIG["icc"]:
        #     self.inter_controller_conn() # UDP Server for Inter Controller Connection

        # No switchmode for basic GVPN, ignore this
        # if CONFIG["switchmode"]:
            # self.arp_table = {}

        # No TURN in barebones GVPN, so ignore this
        # Ignore the network interfaces in the list
        # if "network_ignore_list" in CONFIG:
        #     logging.debug("network ignore list")
        #     make_call(self.sock, m="set_network_ignore_list",\
        #                      network_ignore_list=CONFIG["network_ignore_list"])

        # Register to the XMPP server
        do_set_logging(self.sock, CONFIG["tincan_logging"])
        # Callback endpoint to receive notifications
        do_set_cb_endpoint(self.sock, self.sock.getsockname()) 

        if not CONFIG["router_mode"]:
            do_set_local_ip(self.sock, self.uid, self.ip4, gen_ip6(self.uid),
                            CONFIG["ip4_mask"], CONFIG["ip6_mask"],
                            CONFIG["subnet_mask"], CONFIG["switchmode"])

        else:
            do_set_local_ip(self.sock, self.uid, CONFIG["router_ip"],
                            gen_ip6(self.uid), CONFIG["router_ip4_mask"],
                            CONFIG["router_ip6_mask"], CONFIG["subnet_mask"])

        # Register to the XMPP server
        do_register_service(self.sock, self.user, self.password, self.host) 
        do_set_switchmode(self.sock, CONFIG["switchmode"])
        do_set_trimpolicy(self.sock, CONFIG["trim_enabled"])
        do_get_state(self.sock) # Information about the local node

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

            # signal.pause() sleeps until SIGINT is received
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

	parse_config()
    CFx = CFX()
    set_global_variable_server(CFx)
    # Ignore Status reporting for now

    CFx.initialize()
    CFx.waitForShutdownEvent()
    CFx.terminate()

if __name__ == "__main__":
    main()


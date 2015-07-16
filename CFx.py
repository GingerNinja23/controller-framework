#!/usr/bin/env python
import os
import sys
import json
import signal
import socket
import threading
import importlib
import collections
from ipoplib import *
from CBT import CBT as _CBT
from CFxHandle import CFxHandle

class CFX(object):

    def __init__(self):
       
        with open('config.json') as data_file:
            # Read config.json into an OrderedDict to load the modules in the order
            # in which they appear in config.json
            self.json_data = json.load(data_file,\
                             object_pairs_hook=collections.OrderedDict)

        # Set default config values
        self.CONFIG = CONFIG
        self.parse_config()

        # A dict containing the references to CFxHandles of all CMs
        # Key is the module name 
        self.CFxHandleDict = {} 
        self.idle_peers = {}
        self.user = self.CONFIG["xmpp_username"]
        self.password = self.CONFIG["xmpp_password"] 
        self.host = self.CONFIG["xmpp_host"] 
        self.ip4 = self.CONFIG["ip4"]
        self.uid = gen_uid(self.ip4) # SHA-1 hash
        self.vpn_type = "GroupVPN"
        self.peers_ip4 = {}
        self.peers_ip6 = {}
        self.far_peers = {}
        self.conn_stat = {}
        if socket.has_ipv6:
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.sock_svr = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self.sock_svr.bind((self.CONFIG["localhost6"], self.CONFIG["contr_port"]))
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_svr = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_svr.bind((self.CONFIG["localhost"], self.CONFIG["contr_port"]))
        self.sock.bind(("", 0))
        self.sock_list = [ self.sock, self.sock_svr ]
        self.uid_ip_table = {}
        parts = self.CONFIG["ip4"].split(".")
        ip_prefix = parts[0] + "." + parts[1] + "."

    def submitCBT(self,CBT):

        # Check the recipient of the CBT
        recipient = CBT.recipient

        # Put the CBT in appropriate queue
        self.CFxHandleDict[recipient].CMQueue.put(CBT)

    def load_module(self,module_name):

        if(module_name not in self.loaded_modules):
            # Load dependencies of the module
            self.load_dependencies(module_name)

            # Dynamically importing the modules
            module = importlib.import_module(module_name)
            
            # Get the class with name key from module
            module_class= getattr(module,module_name) 

            _CFxHandle = CFxHandle(self) # Create a CFxHandle object for each module

            # Instantiate the class, with CFxHandle reference and configuration parameters
            instance = module_class(self,_CFxHandle,self.json_data[module_name])

            _CFxHandle.CMInstance = instance
            _CFxHandle.CMConfig = self.json_data[module_name]

            # Store the CFxHandle object references in the dict with module name as the key
            self.CFxHandleDict[module_name] = _CFxHandle

            # Intialize all the CFxHandles which in turn initialize the CMs    
            _CFxHandle.initialize()

            self.loaded_modules.append(module_name)

    def load_dependencies(self,module_name):
        try:
            dependencies = self.json_data[module_name]['dependencies']
            for module in dependencies:
                if(module not in self.loaded_modules):
                    self.load_module(module)
        except:
            pass

    # Return True if the directed graph g has a cycle.
    def detect_cyclic_dependency(self,g):

        path = set()

        def visit(vertex):
            path.add(vertex)
            for neighbour in g.get(vertex, ()):
                if neighbour in path or visit(neighbour):
                    return True
            path.remove(vertex)
            return False

        return any(visit(v) for v in g)


    def initialize(self,):

        print "CFx Loaded. Initializing Modules\n"
        self.loaded_modules = ['CFx']


        dependency_graph = {}
        for key in self.json_data:
            if(key != 'CFx'):
                try:
                    dependency_graph[key]=self.json_data[key]['dependencies']
                except:
                    pass

        if(self.detect_cyclic_dependency(dependency_graph)):
            logging.error("Circular dependency detected in config.json. Exiting")
            sys.exit()

        # Iterating through the modules mentioned in config.json
        for key in self.json_data:
            if (key not in self.loaded_modules):
                #try:
                self.load_module(key)


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
                    self.event.wait(1)
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

    def parse_config(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("-c", help="load configuration from a file",
                            dest="config_file", metavar="config_file")
        parser.add_argument("-u", help="update configuration file if needed",
                            dest="update_config", action="store_true")
        parser.add_argument("-p", help="load remote ip configuration file",
                            dest="ip_config", metavar="ip_config")
        parser.add_argument("-s", help="configuration as json string (overrides configuration from file)",
                            dest="config_string", metavar="config_string")
        parser.add_argument("--pwdstdout", help="use stdout as password stream",
                            dest="pwdstdout", action="store_true")

        args = parser.parse_args()

        if args.config_file:
            # Load the config file
            with open(args.config_file) as f:

                loaded_config = json.load(f)
                # CFx parameters retrieved from config.json
                try:
                    CFxConfig = loaded_config['CFx']
                except KeyError:
                    logging.error("Invalid Config for CFx. Terminating")
                    sys.exit()

            self.CONFIG.update(CFxConfig)
            
        if args.config_string:
            # Load the config string
            loaded_config = json.loads(args.config_string)
            self.CONFIG.update(loaded_config)        

        need_save = setup_config(CONFIG)
        if need_save and args.config_file and args.update_config:
            with open(args.config_file, "w") as f:
                json.dump(self.CONFIG, f, indent=4, sort_keys=True)

        if not ("xmpp_username" in self.CONFIG and "xmpp_host" in self.CONFIG):
            raise ValueError("At least 'xmpp_username' and 'xmpp_host' must be "
                             "specified in config file or string")

        if "xmpp_password" not in self.CONFIG:
            prompt = "\nPassword for %s: " % self.CONFIG["xmpp_username"]
            if args.pwdstdout:
              self.CONFIG["xmpp_password"] = getpass.getpass(prompt, stream=sys.stdout)
            else:
              self.CONFIG["xmpp_password"] = getpass.getpass(prompt)

        if "controller_logging" in self.CONFIG:
            level = getattr(logging, self.CONFIG["controller_logging"])
            logging.basicConfig(level=level)

        if args.ip_config:
            load_peer_ip_config(args.ip_config)

def main():

    CFx = CFX()
    # Ignore Status reporting for now

    CFx.initialize()
    CFx.waitForShutdownEvent()
    CFx.terminate()

if __name__ == "__main__":
    main()


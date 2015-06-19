import json
import logging
from ipoplib import *
from ControllerModule import ControllerModule

# ControllerModule is an abstract class
class TincanHandler(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject
        self.sockList = [self.CFxObject.sock,self.CFxObject.sock_svr]

    def initialize(self):
        
        logging.info("TincanHandler Loaded")
        self.TincanListenerThread = threading.Thread(target = self.__tincan_listener)
        self.TincanListenerThread.setDaemon(True)
        self.TincanListenerThread.start()

    def processCBT(self,cbt): 
        
        # Process the CBT here
        # Analyse CBT. If heavy, run it on another threads
        logging.debug("TincanHandler: Received CBT from "+cbt.initiator)
        # What CBTs to process ?
        # We have do_ functions for all API calls.

    def timer_method(self):
        pass

    def __tincan_listener(self):
        while(True):
            
            #---------------------------------------------------------------
            #| offset(byte) |                                              |
            #---------------------------------------------------------------
            #|      0       | ipop version                                 |
            #|      1       | message type                                 |
            #|      2       | Payload (JSON formatted control message)     |
            #---------------------------------------------------------------
            socks, _, _ = select.select(self.sock_list, [], [], \
                          self.CFxObject.CONFIG["wait_time"])

            if(socks):
                sock_to_read = socks[0]
                data, addr = sock_to_read.recvfrom(self.CFxObject.CONFIG["buf_size"])

                if data[0] != ipop_ver:
                    logging.debug("ipop version mismatch: tincan:{0} controller"
                                  ":{1}" "".format(data[0].encode("hex"), \
                                   ipop_ver.encode("hex")))
                    sys.exit()

                if data[1] == tincan_control:
                    msg = json.loads(data[2:])
                    logging.debug("recv %s %s" % (addr, data[2:]))
                    msg_type = msg.get("type", None)
                    if msg_type == "echo_request":
                        make_remote_call(self.CFxObject.sock_svr, m_type=tincan_control,\
                          dest_addr=addr[0], dest_port=addr[1], payload=None,\
                          type="echo_reply") # Reply to the echo_request 

                    # Should be placed in CFx?
                    if msg_type == "local_state":
                        self.CFxObject.ipop_state = msg

                    elif msg_type == "peer_state" or msg_type == "con_stat" or \
                         msg_type == "con_req" or msg_type == "con_resp":

                        newCBT = self.CFxHandle.createCBT(initiator='TincanHandler',\
                                                          recipient='LinkManager',action='TINCAN_MSG',data=msg)
                        self.CFxHandle.submitCBT(newCBT)

                    # send message is used as "request for start mutual 
                    # connection"
                    # Passed because of all to all topology
                    elif msg_type == "send_msg": 
                        pass
                   
                # For all to all topology, not required.
                # Passed for now
                elif data[1] == tincan_packet:
                    pass
     
                else:
                    logging.error("Unknown type message")
                    logging.debug("{0}".format(data[0:].encode("hex")))
                    sys.exit()


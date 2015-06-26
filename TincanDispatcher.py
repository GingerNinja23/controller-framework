import json
from ipoplib import *
from ControllerModule import ControllerModule

class TincanDispatcher(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        # logCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',recipient='Logger',\
        #                                   action='info',data="TincanDispatcher Loaded")
        # self.CFxHandle.submitCBT(logCBT)
        print "TincanDispatcher loaded"

    def processCBT(self,cbt):

        #logCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',recipient='Logger',\
        #                                  action='debug',data="TincanDispatcher: Received CBT from "\
        #                                  +cbt.initiator)
        #self.CFxHandle.submitCBT(logCBT)

        #---------------------------------------------------------------
        #| offset(byte) |                                              |
        #---------------------------------------------------------------
        #|      0       | ipop version                                 |
        #|      1       | message type                                 |
        #|      2       | Payload (JSON formatted control message)     |
        #---------------------------------------------------------------

        data = cbt.data[0]
        addr = cbt.data[1]
        if data[0] != ipop_ver:
            logCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',recipient='Logger',\
                                        action='debug',data="ipop version mismatch:"+\
                                       "tincan:{0} controller: {1}".format(data[0].encode("hex"),\
                                        ipop_ver.encode("hex")))
            self.CFxHandle.submitCBT(logCBT)
            sys.exit()

        if data[1] == tincan_control:
            msg = json.loads(data[2:])
            logCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',recipient='Logger',\
                                              action='debug',\
                                              data="recv {0} {1}".format(addr, data[2:]))
            self.CFxHandle.submitCBT(logCBT)
            msg_type = msg.get("type", None)
            if msg_type == "echo_request":
                make_remote_call(self.CFxObject.sock_svr, m_type=tincan_control,\
                  dest_addr=addr[0], dest_port=addr[1], payload=None,\
                  type="echo_reply") # Reply to the echo_request 

            elif msg_type == "local_state":
                self.CFxObject.ipop_state = msg

            elif msg_type == "peer_state":
                newCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',\
                                                  recipient='Monitor',action='STORE_PEER_STATE',\
                                                  data=msg)
                self.CFxHandle.submitCBT(newCBT)

            elif msg_type == "con_stat" or msg_type == "con_req" or msg_type == "con_resp":

                newCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',\
                                                  recipient='BaseTopologyManager',action='TINCAN_MSG',\
                                                  data=msg)
                self.CFxHandle.submitCBT(newCBT)

            # send message is used as "request for start mutual 
            # connection"
            # Passed because of all to all topology
            elif msg_type == "send_msg": 
                pass
           
        # If a packet that is destined to yet no p2p connection 
        # established node, the packet as a whole is forwarded to 
        # controller
        #|-------------------------------------------------------------|
        #| offset(byte) |                                              |
        #|-------------------------------------------------------------|
        #|      0       | ipop version                                 |
        #|      1       | message type                                 |
        #|      2       | source uid                                   |
        #|     22       | destination uid                              |
        #|     42       | Payload (Ethernet frame)                     |
        #|-------------------------------------------------------------|
        elif data[1] == tincan_packet:

            # Ignore IPv6 packets for log readability. Most of them are
            # Multicast DNS packets
            if data[54:56] == "\x86\xdd":
                return
            logging.debug("IP packet forwarded \nversion:{0}\nmsg_type:"
                "{1}\nsrc_uid:{2}\ndest_uid:{3}\nsrc_mac:{4}\ndst_mac:{"
                "5}\neth_type:{6}".format(data[0].encode("hex"), \
                data[1].encode("hex"), data[2:22].encode("hex"), \
                data[22:42].encode("hex"), data[42:48].encode("hex"),\
                data[48:54].encode("hex"), data[54:56].encode("hex")))

            if not self.CFxObject.CONFIG["on-demand_connection"]:
                return
            if len(data) < 16:
                return
            self.create_connection_req(data[2:])

        else:
            logCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',recipient='Logger',\
                                              action='error',\
                                              data="Unknown type message")
            self.CFxHandle.submitCBT(logCBT)
            logCBT = self.CFxHandle.createCBT(initiator='TincanDispatcher',recipient='Logger',\
                                              action='debug',\
                                              data="{0}".format(data[0:].encode("hex")))
            self.CFxHandle.submitCBT(logCBT)
            sys.exit()

    def timer_method(self):
        pass


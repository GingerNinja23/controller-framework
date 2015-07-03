from ipoplib import *
from ControllerModule import ControllerModule

class Monitor(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                          action='info',data="Monitor Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt):

        if(cbt.action == 'STORE_PEER_STATE'):
            msg = cbt.data
            msg_type = msg.get("type", None)
            if msg_type == "peer_state": 
                if msg["status"] == "offline" or "stats" not in msg:
                    self.CFxObject.peers[msg["uid"]] = msg
                    self.trigger_conn_request(msg)
                    return
                stats = msg["stats"]
                total_byte = 0
                for stat in stats:
                    total_byte += stat["sent_total_bytes"]
                    total_byte += stat["recv_total_bytes"]
                msg["total_byte"]=total_byte
                logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                                  action='debug',\
                                                  data="self.peers:{0}".format(self.CFxObject.peers))
                self.CFxHandle.submitCBT(logCBT)
                if not msg["uid"] in self.CFxObject.peers:
                    msg["last_active"]=time.time()
                elif not "total_byte" in self.CFxObject.peers[msg["uid"]]:
                    msg["last_active"]=time.time()
                else:
                    if msg["total_byte"] > \
                                 self.CFxObject.peers[msg["uid"]]["total_byte"]:
                        msg["last_active"]=time.time()
                    else:
                        msg["last_active"]=\
                                self.CFxObject.peers[msg["uid"]]["last_active"]
                self.CFxObject.peers[msg["uid"]] = msg

        elif(cbt.action == 'QUERY_PEER_STATE'):
            peer_uid = cbt.data
            cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator
            cbt.data = self.CFxObject.peers.get(peer_uid)
            self.CFxHandle.submitCBT(cbt)

        else:
            logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                              action='error',data="Monitor: Unknown type of CBT "\
                                              "received from: "+cbt.initiator)

    def timer_method(self):
        do_get_state(self.CFxObject.sock)

    def terminate(self):
        pass

    def trigger_conn_request(self, peer):
        if "fpr" not in peer and peer["xmpp_time"] < \
                            self.CFxObject.CONFIG["wait_time"] * 8:                            
            self.CFxObject.conn_stat[peer["uid"]] = "req_sent"
            do_send_msg(self.CFxObject.sock, "con_req", 1, peer["uid"],
                        self.CFxObject.ipop_state["_fpr"])



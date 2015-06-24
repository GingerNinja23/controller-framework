from ipoplib import *
from ControllerModule import ControllerModule

class BaseTopologyManager(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                          action='info',data="BaseTopologyManager Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt): 

        #logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
        #                                  action='debug',data="BaseTopologyManager: Received CBT from "\
        #                                  +cbt.initiator)
        #self.CFxHandle.submitCBT(logCBT)

        if(cbt.action == "TINCAN_MSG"):
            msg = cbt.data
            msg_type = msg.get("type", None)
            if msg_type == "peer_state": 
                if msg["status"] == "offline" or "stats" not in msg:
                    self.peers[msg["uid"]] = msg
                    self.trigger_conn_request(msg)
                    return
                stats = msg["stats"]
                total_byte = 0
                for stat in stats:
                    total_byte += stat["sent_total_bytes"]
                    total_byte += stat["recv_total_bytes"]
                msg["total_byte"]=total_byte
                logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                                  action='debug',data="self.peers:{0}".format(self.peers))
                self.CFxHandle.submitCBT(logCBT)
                if not msg["uid"] in self.peers:
                    msg["last_active"]=time.time()
                elif not "total_byte" in self.peers[msg["uid"]]:
                    msg["last_active"]=time.time()
                else:
                    if msg["total_byte"] > \
                                 self.peers[msg["uid"]]["total_byte"]:
                        msg["last_active"]=time.time()
                    else:
                        msg["last_active"]=\
                                self.peers[msg["uid"]]["last_active"]
                self.peers[msg["uid"]] = msg

            # we ignore connection status notification for now
            elif msg_type == "con_stat": pass

            elif msg_type == "con_req": 
                if CONFIG["on-demand_connection"]: 
                    self.CFxObject.idle_peers[msg["uid"]]=msg
                else:
                    if self.check_collision(msg_type,msg["uid"]): 
                        return
                    fpr_len = len(self.CFxObject.ipop_state["_fpr"])
                    fpr = msg["data"][:fpr_len]
                    cas = msg["data"][fpr_len + 1:]
                    ip4 = self.CFxObject.uid_ip_table[msg["uid"]]
                    self.create_connection(msg["uid"], fpr, 1, 
                                           CONFIG["sec"], cas, ip4)

            elif msg_type == "con_resp":
                if self.check_collision(msg_type, msg["uid"]): return
                fpr_len = len(self.CFxObject.ipop_state["_fpr"])
                fpr = msg["data"][:fpr_len]
                cas = msg["data"][fpr_len + 1:]
                ip4 = self.CFxObject.uid_ip_table[msg["uid"]]
                self.create_connection(msg["uid"], fpr, 1, 
                                       self.CFxObject.CONFIG["sec"], cas, ip4)

        else:
            logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                              action='warning',data="BaseTopologyManager: Invalid CBT received from "\
                                              +cbt.initiator)
            self.CFxHandle.submitCBT(logCBT)

    def trigger_conn_request(self, peer):
        if "fpr" not in peer and peer["xmpp_time"] < \
                            self.CFxObject.CONFIG["wait_time"] * 8:                            
            self.CFxObject.conn_stat[peer["uid"]] = "req_sent"
            do_send_msg(self.CFxObject.sock, "con_req", 1, peer["uid"],
                        self.CFxObject.ipop_state["_fpr"])

    def create_connection(self, uid, data, nid, sec, cas, ip4):
        do_create_link(self.CFxObject.sock, uid, data, nid, sec, cas)
        if (self.CFxObject.CONFIG["switchmode"] == 1):
            do_set_remote_ip(self.CFxObject.sock, uid, ip4, gen_ip6(uid))
        else: 
            do_set_remote_ip(self.CFxObject.sock, uid, ip4, gen_ip6(uid))

    def check_collision(self, msg_type, uid):
        if msg_type == "con_req" and \
           self.CFxObject.conn_stat.get(uid, None) == "req_sent":
            if uid > self.CFxObject.ipop_state["_uid"]:
                do_trim_link(self.CFxObject.sock, uid)
                self.CFxObject.conn_stat.pop(uid, None)
            return False
        elif msg_type == "con_resp":
            self.CFxObject.conn_stat[uid] = "resp_recv"
            return False
        else:
            return True

    def __link_trimmer():
        for k, v in self.CFxObject.peers.iteritems():
            # Trim TinCan link if the peer is offline
            if "fpr" in v and v["status"] == "offline":
                if v["last_time"] > self.CFxObject.CONFIG["wait_time"] * 2:
                    do_send_msg(self.CFxObject.sock, "send_msg", 1, k,
                                "destroy" + self.CFxObject.ipop_state["_uid"])
                    do_trim_link(self.CFxObject.sock, k)
            # Trim TinCan link if the On Demand Inactive Timeout occurs        
            if self.CFxObject.CONFIG["on-demand_connection"] and v["status"] == "online": 
                if v["last_active"] + self.CFxObject.CONFIG["on-demand_inactive_timeout"]\
                                                              < time.time():
                    logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                                      action='debug',data="Inactive, trimming node:{0}".format(k)\
                                                      +cbt.initiator)
                    self.CFxHandle.submitCBT(logCBT)
                    do_send_msg(self.CFxObject.sock, 1, "send_msg", k,
                                "destroy" + self.CFxObject.ipop_state["_uid"])
                    do_trim_link(self.CFxObject.sock, k)

    def timer_method(self):
        self.__link_trimmer()

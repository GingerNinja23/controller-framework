from ipoplib import *
from ControllerModule import ControllerModule

class BaseTopologyManager(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        # logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
        #                                   action='info',data="BaseTopologyManager Loaded")
        # self.CFxHandle.submitCBT(logCBT)

        print "BaseTopologyManager loaded"

    def processCBT(self,cbt): 

        #logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
        #                                  action='debug',data="BaseTopologyManager: Received CBT from "\
        #                                  +cbt.initiator)
        #self.CFxHandle.submitCBT(logCBT)

        if(cbt.action == "TINCAN_MSG"):
            msg = cbt.data
            msg_type = msg.get("type", None)

            # we ignore connection status notification for now
            if msg_type == "con_stat": pass

            elif msg_type == "con_req": 
                if self.CFxObject.CONFIG["on-demand_connection"]: 
                    self.CFxObject.idle_peers[msg["uid"]]=msg
                else:
                    if self.check_collision(msg_type,msg["uid"]): 
                        return
                    fpr_len = len(self.CFxObject.ipop_state["_fpr"])
                    fpr = msg["data"][:fpr_len]
                    cas = msg["data"][fpr_len + 1:]
                    ip4 = self.CFxObject.uid_ip_table[msg["uid"]]
                    self.create_connection(msg["uid"], fpr, 1, 
                                           self.CFxObject.CONFIG["sec"], cas, ip4)

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
                                              action='warning'\
                                              ,data="BaseTopologyManager: Invalid CBT received "\
                                              "from "+cbt.initiator)
            self.CFxHandle.submitCBT(logCBT)

    def create_connection(self, uid, data, nid, sec, cas, ip4):
        # locals() returns a dict of all the local varibles of the function present
        # at the instant when the function is called
        createLinkCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                 recipient='LinkManager',action='CREATE_LINK',\
                                                 data=locals())
        self.CFxHandle.submitCBT(createLinkCBT)
        if (self.CFxObject.CONFIG["switchmode"] == 1):
            do_set_remote_ip(self.CFxObject.sock, uid, ip4, gen_ip6(uid))
        else: 
            do_set_remote_ip(self.CFxObject.sock, uid, ip4, gen_ip6(uid))

    def check_collision(self, msg_type, uid):
        if msg_type == "con_req" and \
           self.CFxObject.conn_stat.get(uid, None) == "req_sent":
            if uid > self.CFxObject.ipop_state["_uid"]:
                trimCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                   recipient='LinkManager',action='TRIM_LINK',\
                                                   data=uid)
                self.CFxHandle.submitCBT(trimCBT)
                self.CFxObject.conn_stat.pop(uid, None)
            return False
        elif msg_type == "con_resp":
            self.CFxObject.conn_stat[uid] = "resp_recv"
            return False
        else:
            return True

    def __link_trimmer(self):
        for k, v in self.CFxObject.peers.iteritems():
            # Trim TinCan link if the peer is offline
            if "fpr" in v and v["status"] == "offline":
                if v["last_time"] > self.CFxObject.CONFIG["wait_time"] * 2:
                    do_send_msg(self.CFxObject.sock, "send_msg", 1, k,
                                "destroy" + self.CFxObject.ipop_state["_uid"])
                    trimCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                       recipient='LinkManager',action='TRIM_LINK',\
                                                       data=k)
                    self.CFxHandle.submitCBT(trimCBT)
    
            # Trim TinCan link if the On Demand Inactive Timeout occurs        
            if self.CFxObject.CONFIG["on-demand_connection"] and v["status"] == "online": 
                if v["last_active"] + self.CFxObject.CONFIG["on-demand_inactive_timeout"]\
                                                              < time.time():
                    logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                      recipient='Logger',action='debug',\
                                                      data="Inactive, trimming node:{0}".format(k)\
                                                      +cbt.initiator)
                    self.CFxHandle.submitCBT(logCBT)
                    do_send_msg(self.CFxObject.sock, 1, "send_msg", k,
                                "destroy" + self.CFxObject.ipop_state["_uid"])
                    trimCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                       recipient='LinkManager',action='TRIM_LINK',\
                                                       data=k)
                    self.CFxHandle.submitCBT(trimCBT)

    def timer_method(self):
        self.__link_trimmer()

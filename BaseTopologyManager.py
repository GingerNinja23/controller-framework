from ipoplib import *
from ControllerModule import ControllerModule

class BaseTopologyManager(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                          recipient='Logger',\
                                          action='info',\
                                          data="BaseTopologyManager Loaded")
        self.CFxHandle.submitCBT(logCBT)

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
                logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                                  action='info',\
                                                  data="Received connection request")
                self.CFxHandle.submitCBT(logCBT)
                if self.CFxObject.CONFIG["on-demand_connection"]: 
                  idle_peer_CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Monitor',\
                                                    action='STORE_IDLE_PEER_STATE',\
                                                    data={'uid':msg['uid'],'idle_peer_state':msg})
                  self.CFxHandle.submitCBT(logCBT)
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
                logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                              action='warning'\
                                              ,data="Receive connection response")
                self.CFxHandle.submitCBT(logCBT)
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

        conn_dict = {'uid':uid,'fpr':data,'nid':nid,'sec':sec,'cas':cas}
        createLinkCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                 recipient='LinkManager',action='CREATE_LINK',\
                                                 data=conn_dict)
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

    def terminate(self):
        pass



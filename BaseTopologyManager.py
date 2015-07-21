from ipoplib import *
from ControllerModule import ControllerModule

class BaseTopologyManager(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CBTMappings = {}
        self.CFxObject = CFxObject
        self.ipop_state = None

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                          recipient='Logger',\
                                          action='info',\
                                          data="BaseTopologyManager Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt):
        # In case of a fresh CBT, request the required services
        # from the other modules, by issuing CBTs. If no services
        # from other modules required, process the CBT here only
        if((cbt not in self.pendingCBT) and not self.checkMapping(cbt)):
            if(cbt.action == "TINCAN_MSG"):
                msg = cbt.data
                msg_type = msg.get("type", None)

                # we ignore connection status notification for now
                if msg_type == "con_stat":
                    pass

                elif msg_type == "con_req":
                    stateCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                        recipient='Watchdog',\
                                                        action='QUERY_IPOP_STATE',\
                                                        data="")
                    self.CFxHandle.submitCBT(stateCBT)
                    self.CBTMappings[cbt.uid] = [stateCBT.uid]

                    mappingCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                        recipient='AddressMapper',\
                                                        action='RESOLVE',\
                                                        data=msg['uid'])
                    self.CFxHandle.submitCBT(mappingCBT)
                    self.CBTMappings[cbt.uid].append(mappingCBT.uid)

                    conn_stat_CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                        recipient='Monitor',\
                                                        action='QUERY_CONN_STAT',\
                                                        data=msg['uid'])
                    self.CFxHandle.submitCBT(mappingCBT)
                    self.CBTMappings[cbt.uid].append(conn_stat_CBT.uid)

                    self.pendingCBT[cbt.uid] = cbt

                elif msg_type == "con_resp":

                    stateCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                        recipient='Watchdog',\
                                                        action='QUERY_IPOP_STATE',\
                                                        data="")
                    self.CFxHandle.submitCBT(stateCBT)
                    self.CBTMappings[cbt.uid] = [stateCBT.uid]

                    mappingCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                        recipient='AddressMapper',\
                                                        action='RESOLVE',\
                                                        data=msg['uid'])
                    self.CFxHandle.submitCBT(mappingCBT)
                    self.CBTMappings[cbt.uid].append(mappingCBT.uid)


                    conn_stat_CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                        recipient='Monitor',\
                                                        action='QUERY_CONN_STAT',\
                                                        data=msg['uid'])
                    self.CFxHandle.submitCBT(mappingCBT)
                    self.CBTMappings[cbt.uid].append(conn_stat_CBT.uid)
                    self.pendingCBT[cbt.uid] = cbt

            else:
                logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                                  action='warning'\
                                                  ,data="BaseTopologyManager: Invalid CBT received "\
                                                  "from "+cbt.initiator)
                self.CFxHandle.submitCBT(logCBT)

        # Case when one of the requested service CBT comes back
        elif((cbt not in self.pendingCBT) and self.checkMapping(cbt)):
            # Get the source CBT of this request
            sourceCBT_uid = self.checkMapping(cbt)
            self.pendingCBT[cbt.uid]=cbt
            # If all the other services of this sourceCBT are also completed,
            # process CBT here. Else wait for other CBTs to arrive 
            if(self.allServicesCompleted(sourceCBT_uid)):
                if(self.pendingCBT[sourceCBT_uid]['action'] == 'TINCAN_MSG'):
                    if msg_type == "con_req":
                        for key in self.pendingCBT:
                            if(self.pendingCBT[key]['action'] == 'QUERY_IPOP_STATE'):
                                self.ipop_state = self.pendingCBT[key]['data']
                            elif(self.pendingCBT[key]['action'] == 'RESOLVE'):
                                ip4 = self.pendingCBT[key]['data']
                            elif(self.pendingCBT[key]['action'] == 'QUERY_CONN_STAT'):
                                conn_stat = cbt.data

                        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                          recipient='Logger',\
                                                          action='info',\
                                                          data="Received connection request")
                        self.CFxHandle.submitCBT(logCBT)

                        if self.CFxObject.CONFIG["on-demand_connection"]: 
                            idle_peer_CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                           recipient='Monitor',\
                                                           action='STORE_IDLE_PEER_STATE',\
                                                           data={'uid':msg['uid'],'idle_peer_state':msg})
                            self.CFxHandle.submitCBT(logCBT)

                        else:
                            if self.check_collision(msg_type,msg["uid"], conn_stat): 
                                return
                            fpr_len = len(self.ipop_state["_fpr"])
                            fpr = msg["data"][:fpr_len]
                            cas = msg["data"][fpr_len + 1:]
                            self.create_connection(msg["uid"], fpr, 1, 
                                                   self.CFxObject.CONFIG["sec"], cas, ip4)

                    elif msg_type == "con_resp":
                        for key in self.pendingCBT:
                            if(self.pendingCBT[key]['action'] == 'QUERY_IPOP_STATE'):
                                self.ipop_state = self.pendingCBT[key]['data']
                            elif(self.pendingCBT[key]['action'] == 'RESOLVE'):
                                ip4 = self.pendingCBT[key]['data']
                            elif(self.pendingCBT[key]['action'] == 'QUERY_CONN_STAT'):
                                conn_stat = cbt.data

                        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                          recipient='Logger',\
                                                          action='warning',\
                                                          data="Receive connection response")
                        self.CFxHandle.submitCBT(logCBT)

                        if self.check_collision(msg_type, msg["uid"],conn_stat): return
                        fpr_len = len(self.ipop_state["_fpr"])
                        fpr = msg["data"][:fpr_len]
                        cas = msg["data"][fpr_len + 1:]
                        self.create_connection(msg["uid"], fpr, 1, 
                                               self.CFxObject.CONFIG["sec"], cas, ip4)

        else:
            logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',recipient='Logger',\
                                              action='error',\
                                              data="BaseTopologyManager: CBT already exists in "\
                                              "pendingCBT dictionary")
            self.CFxHandle.submitCBT(logCBT)

    # Check if the given cbt is a request sent by the current module
    # If yes, returns the source CBT for which the request has been
    # created, else return None
    def checkMapping(self,cbt):
        for key in self.CBTMappings:
            if(cbt.uid in self.CBTMappings[key]):
                return key
        return None

    # For a given sourceCBT's uid, check if all requests are serviced
    def allServicesCompleted(self,sourceCBT_uid):
        requested_services = self.CBTMappings[sourceCBT_uid]
        for service in requested_services:
            if(service not in self.pendingCBT):
                return False
        return True

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

    def check_collision(self, msg_type, uid, conn_stat):
        if msg_type == "con_req" and \
           conn_stat == "req_sent":
            if uid > self.ipop_state["_uid"]:
                trimCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                   recipient='LinkManager',action='TRIM_LINK',\
                                                   data=uid)
                self.CFxHandle.submitCBT(trimCBT)

                conn_stat_pop_CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                                   recipient='Monitor',action='DELETE_CONN_STAT',\
                                                   data=uid)
                self.CFxHandle.submitCBT(conn_stat_pop_CBT)
            return False
        elif msg_type == "con_resp":
            conn_stat_CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',\
                                               recipient='Monitor',action='STORE_CONN_STAT',\
                                               data={'uid':uid,'status':"resp_recv"})
            self.CFxHandle.submitCBT(conn_stat_CBT)
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



from ipoplib import *
from ControllerModule import ControllerModule

class Monitor(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CBTMappings = {}
        self.peers = {}
        self.conn_stat = {}
        self.ipop_state = None

    def initialize(self):
        
        logCBT = self.CFxHandle.createCBT(initiator='Monitor',\
                                          recipient='Logger',\
                                          action='info',\
                                          data="Monitor Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self,cbt):

        # In case of a fresh CBT, request the required services
        # from the other modules, by issuing CBTs. If no services
        # from other modules required, process the CBT here only
        if((cbt not in self.pendingCBT) and not checkMapping(cbt)):
            if(cbt.action == 'STORE_PEER_STATE'):
                stateCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Watchdog',\
                                                  action='QUERY_IPOP_STATE',\
                                                  data="")
                self.CFxHandle.submitCBT(stateCBT)
                self.CBTMappings[cbt.uid] = [stateCBT.uid]
                self.pendingCBT[cbt.uid] = cbt

            elif(cbt.action == 'QUERY_PEER_STATE'):
                peer_uid = cbt.data
                cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator
                cbt.data = self.peers.get(peer_uid)
                self.CFxHandle.submitCBT(cbt)

            else:
                logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                                  action='error',\
                                                  data="Monitor: Unknown type of CBT "\
                                                  "received from: "+cbt.initiator)
                self.CFxHandle.submitCBT(logCBT)

        # Case when one of the requested service CBT comes back
        elif((cbt not in self.pendingCBT) and checkMapping(cbt)):
            # Get the source CBT of this request
            sourceCBT_uid = checkMapping(cbt)
            # If all the other services of this sourceCBT are also completed,
            # process CBT here. Else wait for other CBTs to arrive 
            if(allServicesCompleted(sourceCBT_uid)):
                if(pendingCBT[sourceCBT_uid]['action'] == 'STORE_PEER_STATE'):
                    for key in pendingCBT:
                        if(pendingCBT[key]['action'] == 'QUERY_IPOP_STATE'):
                            self.ipop_state = pendingCBT[key]['data']
      
                    msg = pendingCBT[sourceCBT_uid].data
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
                        logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                                          action='debug',\
                                                          data="self.peers:{0}".format(self.peers))
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
            
            else:
                self.pendingCBT[cbt.uid]=cbt

        else:
            logCBT = self.CFxHandle.createCBT(initiator='Monitor',recipient='Logger',\
                                              action='error',\
                                              data="Monitor: CBT already exists in "\
                                              "pendingCBT dictionary")
            self.CFxHandle.submitCBT(logCBT)

    def timer_method(self):
        pass

    def terminate(self):
        pass

    # Check if the given cbt is a request sent by the current module
    # If yes, returns the source CBT for which the request has been
    # created, else return None
    def checkMapping(self,cbt):
        for key in self.CBTMappings:
            if(cbt.data.uid in self.CBTMappings[key]):
                return key
        return None

    # For a given sourceCBT's uid, check if all requests are serviced
    def allServicesCompleted(self,sourceCBT_uid):
        requested_services = CBTMappings[sourceCBT_uid]
        for service in requested_services:
            if(service not in pendingCBT):
                return False
        return True


    def trigger_conn_request(self, peer):
        if "fpr" not in peer and peer["xmpp_time"] < \
                            self.CFxObject.CONFIG["wait_time"] * 8:                            
            self.conn_stat[peer["uid"]] = "req_sent"
            do_send_msg(self.CFxObject.sock, "con_req", 1, peer["uid"],
                        self.ipop_state["_fpr"])



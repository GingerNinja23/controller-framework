import time
from ControllerModule import ControllerModule


class Monitor(ControllerModule):

    def __init__(self, CFxHandle, paramDict):

        super(Monitor, self).__init__()
        self.CFxHandle = CFxHandle
        self.CMConfig = paramDict
        self.peers = {}
        self.idle_peers = {}
        self.peers_ip4 = {}
        self.peers_ip6 = {}
        self.conn_stat = {}
        self.ipop_state = None

    def initialize(self):

        logCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                          recipient='Logger',
                                          action='info',
                                          data="Monitor Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self, cbt):

        # In case of a fresh CBT, request the required services
        # from the other modules, by issuing CBTs. If no services
        # from other modules required, process the CBT here only

        if(not self.checkMapping(cbt)):

            if(cbt.action == 'STORE_PEER_STATE'):

                # Storing peer state requires ipop_state, which
                # is requested by sending a CBT to Watchdog
                stateCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                                    recipient='Watchdog',
                                                    action='QUERY_IPOP_STATE',
                                                    data="")
                self.CFxHandle.submitCBT(stateCBT)

                # Maintain a mapping of the source CBT and issued CBTs
                self.CBTMappings[cbt.uid] = [stateCBT.uid]

                # Put this CBT in pendingCBT dict, since it hasn't been
                # processed yet
                self.pendingCBT[cbt.uid] = cbt

            elif(cbt.action == 'QUERY_PEER_STATE'):

                # Respond to a CM requesting state of a particular peer

                peer_uid = cbt.data
                cbt.action = 'QUERY_PEER_STATE_RESP'
                cbt.initiator, cbt.recipient = cbt.recipient, cbt.initiator
                cbt.data = self.peers.get(peer_uid)
                self.CFxHandle.submitCBT(cbt)

            elif(cbt.action == 'QUERY_PEER_LIST'):

                # Respond to a CM requesting state of a particular peer

                cbt.action = 'QUERY_PEER_LIST_RESP'
                cbt.initiator, cbt.recipient = cbt.recipient, cbt.initiator
                cbt.data = self.peers
                self.CFxHandle.submitCBT(cbt)

            elif(cbt.action == 'QUERY_CONN_STAT'):

                # Respond to a CM requesting conn_stat of a particular peer
                uid = cbt.data
                cbt.action = 'QUERY_CONN_STAT_RESP'
                cbt.initiator, cbt.recipient = cbt.recipient, cbt.initiator
                cbt.data = self.conn_stat.get(uid)
                self.CFxHandle.submitCBT(cbt)

            elif(cbt.action == 'DELETE_CONN_STAT'):

                # Delete conn_stat of a given peer on request from another CM
                uid = cbt.data
                self.conn_stat.pop(uid, None)

            elif(cbt.action == 'STORE_CONN_STAT'):

                # Store conn_stat of a given peer
                try:
                    self.conn_stat[cbt.data['uid']] = cbt.data['status']
                except KeyError:
                    logCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                                      recipient='Logger',
                                                      action='warning',
                                                      data="Invalid "
                                                      "STORE_CONN_STAT"
                                                      " Configuration"
                                                      " from " + cbt.initiator)
                    self.CFxHandle.submitCBT(logCBT)

            elif(cbt.action == 'QUERY_IDLE_PEER_LIST'):

                # Respond to a CM requesting for idle peer list
                cbt.action = 'QUERY_IDLE_PEER_LIST_RESP'
                cbt.initiator, cbt.recipient = cbt.recipient, cbt.initiator
                cbt.data = self.idle_peers
                self.CFxHandle.submitCBT(cbt)

            elif(cbt.action == 'STORE_IDLE_PEER_STATE'):

                # Store state of a given idle peer
                try:
                    # cbt.data is a dict with uid and idle_peer_state keys
                    self.idle_peers[cbt.data['uid']] = \
                                    cbt.data['idle_peer_state']
                except KeyError:

                    logCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                                      recipient='Logger',
                                                      action='warning',
                                                      data="Invalid "
                                                      "STORE_IDLE_PEER_STATE"
                                                      " Configuration")
                    self.CFxHandle.submitCBT(logCBT)

            else:
                logCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                                  recipient='Logger',
                                                  action='error',
                                                  data="Monitor: Unrecognized "
                                                  "CBT from: " + cbt.initiator)
                self.CFxHandle.submitCBT(logCBT)

        # Case when one of the requested service CBT comes back
        elif(self.checkMapping(cbt)):

            # Get the source CBT of this response CBT
            sourceCBT_uid = self.checkMapping(cbt)
            self.pendingCBT[cbt.uid] = cbt

            # If all the other services of this sourceCBT are also completed,
            # process CBT here. Else wait for other CBTs to arrive
            if(self.allServicesCompleted(sourceCBT_uid)):
                if(self.pendingCBT[sourceCBT_uid].action ==
                        'STORE_PEER_STATE'):

                    # Retrieve values from response CBTs
                    for key in self.CBTMappings[sourceCBT_uid]:
                        if(self.pendingCBT[key].action == 'QUERY_IPOP_STATE_RESP'):
                            self.ipop_state = self.pendingCBT[key].data

                    # Process the source CBT, once all the required variables
                    # are extracted from the response CBTs

                    msg = self.pendingCBT[sourceCBT_uid].data
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
                        msg["total_byte"] = total_byte
                        logCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                                          recipient='Logger',
                                                          action='debug',
                                                          data="self.peers:{0}"
                                                          .format(self.peers))
                        self.CFxHandle.submitCBT(logCBT)
                        if not msg["uid"] in self.peers:
                            msg["last_active"] = time.time()
                        elif not "total_byte" in self.peers[msg["uid"]]:
                            msg["last_active"] = time.time()
                        else:
                            if msg["total_byte"] > \
                                         self.peers[msg["uid"]]["total_byte"]:
                                msg["last_active"] = time.time()
                            else:
                                msg["last_active"] = \
                                        self.peers[msg["uid"]]["last_active"]
                        self.peers[msg["uid"]] = msg

        else:
            logCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                              recipient='Logger',
                                              action='error',
                                              data="Monitor: CBT already"
                                              " exists in pendingCBT "
                                              "dictionary")
            self.CFxHandle.submitCBT(logCBT)

    def timer_method(self):
        pass

    def trigger_conn_request(self, peer):
        if "fpr" not in peer and peer["xmpp_time"] < \
                self.CMConfig["trigger_con_wait_time"]:
            self.conn_stat[peer["uid"]] = "req_sent"

            cbtData = {
                "method": "con_req",
                "overlay_id": 1,
                "uid": peer["uid"],
                "data": self.ipop_state["_fpr"]
            }

            TincanCBT = self.CFxHandle.createCBT(initiator='Monitor',
                                                 recipient='TincanSender',
                                                 action='DO_SEND_MSG',
                                                 data=cbtData)
            self.CFxHandle.submitCBT(TincanCBT)

    def terminate(self):
        pass

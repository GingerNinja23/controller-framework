import time
import socket
import struct
import ipoplib
from ControllerModule import ControllerModule


class BaseTopologyManager(ControllerModule):

    def __init__(self, CFxHandle, paramDict):

        super(BaseTopologyManager, self).__init__()
        self.CFxHandle = CFxHandle
        self.CMConfig = paramDict
        self.ipop_state = None

    def initialize(self):

        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',
                                          recipient='Logger',
                                          action='info',
                                          data="BaseTopologyManager Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self, cbt):

        # In case of a fresh CBT, request the required services
        # from the other modules, by issuing CBTs. If no services
        # from other modules required, process the CBT here only

        if(not self.checkMapping(cbt)):
            if(cbt.action == "TINCAN_MSG"):
                msg = cbt.data
                msg_type = msg.get("type", None)

                # we ignore connection status notification for now
                if msg_type == "con_stat":
                    pass

                elif msg_type == "con_req" or msg_type == "con_resp":
                    stateCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                        'Manager',
                                                        recipient='Watchdog',
                                                        action='QUERY_IPOP_STATE',
                                                        data="")
                    self.CFxHandle.submitCBT(stateCBT)
                    self.CBTMappings[cbt.uid] = [stateCBT.uid]

                    mapCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                      'Manager',
                                                      recipient='Address'
                                                      'Mapper',
                                                      action='RESOLVE',
                                                      data=msg['uid'])
                    self.CFxHandle.submitCBT(mapCBT)
                    self.CBTMappings[cbt.uid].append(mapCBT.uid)

                    conn_stat_CBT = self.CFxHandle.createCBT(initiator='Base'
                                                             'TopologyManager',
                                                             recipient='Monitor',
                                                             action='QUERY_'
                                                             'CONN_STAT',
                                                             data=msg['uid'])
                    self.CFxHandle.submitCBT(conn_stat_CBT)
                    self.CBTMappings[cbt.uid].append(conn_stat_CBT.uid)
                    self.pendingCBT[cbt.uid] = cbt

                # send message is used as "request for start mutual
                # connection"
                elif msg_type == "send_msg":
                    idle_peer_CBT = self.CFxHandle.createCBT(initiator='Base'
                                                             'TopologyManager',
                                                             recipient='Monitor',
                                                             action='QUERY_'
                                                             'IDLE_PEER_LIST',
                                                             data="")
                    self.CFxHandle.submitCBT(idle_peer_CBT)
                    self.CBTMappings[cbt.uid] = [idle_peer_CBT.uid]
                    self.pendingCBT[cbt.uid] = cbt

            elif(cbt.action == "TINCAN_PACKET"):

                idle_peer_CBT = self.CFxHandle.createCBT(initiator='Base'
                                                         'TopologyManager',
                                                         recipient='Monitor',
                                                         action='QUERY_'
                                                         'IDLE_PEER_LIST',
                                                         data="")
                self.CFxHandle.submitCBT(idle_peer_CBT)
                self.CBTMappings[cbt.uid] = [idle_peer_CBT.uid]
                self.pendingCBT[cbt.uid] = cbt

            elif(cbt.action == "ICC_MSG"):
                msg = cbt.data
                msg_type = msg.get("msg_type", None)

            elif(cbt.action == "LINK_TRIMMER"):
                stateCBT = self.CFxHandle.createCBT(initiator='Base'
                                                    'TopologyManager',
                                                    recipient='Watchdog',
                                                    action='QUERY_IPOP_STATE',
                                                    data="")
                self.CFxHandle.submitCBT(stateCBT)

                peersCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                    'Manager',
                                                    recipient='Monitor',
                                                    action='QUERY_PEER_LIST',
                                                    data='')
                self.CFxHandle.submitCBT(peersCBT)

                self.pendingCBT[cbt.uid] = cbt
                self.CBTMappings[cbt.uid] = [stateCBT.uid, peersCBT.uid]

            elif(cbt.action == "ONDEMAND_CONNECTION"):

                try:
                    mapCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                      'Manager',
                                                      recipient='Address'
                                                      'Mapper',
                                                      action='RESOLVE',
                                                      data=cbt.data['uid'])
                    self.CFxHandle.submitCBT(mapCBT)
                    self.CBTMappings[cbt.uid] = [mapCBT.uid]
                    self.pendingCBT[cbt.uid] = cbt

                except:
                    logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',
                                                      recipient='Logger',
                                                      action='warning',
                                                      data="Invalid UID received"
                                                      " for ONDEMAND_CONNECTION")
                    self.CFxHandle.submitCBT(logCBT)

            else:
                logCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                  'Manager',
                                                  recipient='Logger',
                                                  action='warning',
                                                  data="BaseTopologyManager:"
                                                  " Unrecognized CBT "
                                                  "from " + cbt.initiator)
                self.CFxHandle.submitCBT(logCBT)

        # Case when one of the requested service CBT comes back
        elif(self.checkMapping(cbt)):
            # Get the source CBT of this request
            sourceCBT_uid = self.checkMapping(cbt)
            self.pendingCBT[cbt.uid] = cbt
            # If all the other services of this sourceCBT are also completed,
            # process CBT here. Else wait for other CBTs to arrive
            if(self.allServicesCompleted(sourceCBT_uid)):
                if(self.pendingCBT[sourceCBT_uid].action == 'TINCAN_MSG'):
                    msg = self.pendingCBT[sourceCBT_uid].data
                    msg_type = msg.get("type", None)
                    if msg_type == "con_req":
                        for key in self.CBTMappings[sourceCBT_uid]:
                            if(self.pendingCBT[key].action ==
                                    'QUERY_IPOP_STATE_RESP'):
                                self.ipop_state = self.pendingCBT[key].data
                            elif(self.pendingCBT[key].action ==
                                    'RESOLVE_RESP'):
                                ip4 = self.pendingCBT[key].data
                            elif(self.pendingCBT[key].action ==
                                    'QUERY_CONN_STAT_RESP'):
                                conn_stat = cbt.data

                        logCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                          'Manager',
                                                          recipient='Logger',
                                                          action='info',
                                                          data="Received"
                                                          " connection request")
                        self.CFxHandle.submitCBT(logCBT)

                        if self.CMConfig["on-demand_connection"]:
                            idle_peer_CBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                                     'Manager',
                                                                     recipient='Monitor',
                                                                     action='STORE_IDLE_'
                                                                     'PEER_STATE',
                                                                     data={'uid': msg['uid'],
                                                                            'idle_'
                                                                            'peer_state': msg})
                            self.CFxHandle.submitCBT(idle_peer_CBT)

                        else:
                            if self.check_collision(msg_type, msg["uid"], conn_stat):
                                return
                            fpr_len = len(self.ipop_state["_fpr"])
                            fpr = msg["data"][:fpr_len]
                            cas = msg["data"][fpr_len + 1:]
                            self.create_connection(msg["uid"], fpr, 1,
                                                   self.CMConfig["sec"], cas, ip4)

                    elif msg_type == "con_resp":
                        for key in self.CBTMappings[sourceCBT_uid]:
                            if(self.pendingCBT[key].action ==
                                    'QUERY_IPOP_STATE'):
                                self.ipop_state = self.pendingCBT[key].data
                            elif(self.pendingCBT[key].action ==
                                    'RESOLVE_RESP'):
                                ip4 = self.pendingCBT[key].data
                            elif(self.pendingCBT[key].action ==
                                    'QUERY_CONN_STAT_RESP'):
                                conn_stat = cbt.data

                        logCBT = self.CFxHandle.createCBT(initiator='Base'
                                                          'TopologyManager',
                                                          recipient='Logger',
                                                          action='warning',
                                                          data="Received "
                                                          "connection"
                                                          " response")
                        self.CFxHandle.submitCBT(logCBT)

                        if self.check_collision(msg_type, msg["uid"], conn_stat):
                            return
                        fpr_len = len(self.ipop_state["_fpr"])
                        fpr = msg["data"][:fpr_len]
                        cas = msg["data"][fpr_len + 1:]
                        self.create_connection(msg["uid"], fpr, 1,
                                               self.CMConfig["sec"], cas, ip4)

                    elif msg_type == "send_msg":
                        for key in self.CBTMappings[sourceCBT_uid]:
                            if(self.pendingCBT[key].action == 'QUERY_IDLE_PEER_LIST_RESP'):
                                idle_peers = self.pendingCBT[key].data
                        if self.CMConfig["on-demand_connection"]:
                            if msg["data"].startswith("destroy"):
                                TincanCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                                     'Manager',
                                                                     recipient='TincanSender',
                                                                     action='DO_TRIM_LINK',
                                                                     data=msg["uid"])
                                self.CFxHandle.submitCBT(TincanCBT)
                            else:
                                cbt_data = {
                                    'uid': msg["uid"],
                                    'idle_peers': idle_peers,
                                    'send_req': False
                                }

                                CBT = self.CFxHandle.createCBT(initiator='Base'
                                                               'Topology'
                                                               'Manager',
                                                               recipient='Base'
                                                               'Topology'
                                                               'Manager',
                                                               action='ONDEMA'
                                                               'ND_CONNECTION',
                                                               data=cbt_data)
                                self.CFxHandle.submitCBT(CBT)

                elif(self.pendingCBT[sourceCBT_uid].action == 'TINCAN_PACKET'):
                    for key in self.CBTMappings[sourceCBT_uid]:
                        if(self.pendingCBT[key].action ==
                           'QUERY_IDLE_PEER_LIST_RESP'):
                            idle_peers = self.pendingCBT[key].data
                    data = self.pendingCBT[sourceCBT_uid].data

                    # Ignore IPv6 packets for log readability. Most of them are
                    # Multicast DNS packets
                    if data[54:56] == "\x86\xdd":
                        return

                    log_str = "IP packet forwarded \nversion:{0}"\
                              "\nmsg_type:{1}\nsrc_uid:{2}\n"\
                              "dest_uid:{3}\nsrc_mac:{4}\ndst_mac:{5}\n"\
                              "eth_type:{6}".format(data[0].encode("hex"),
                                                    data[1].encode("hex"),
                                                    data[2:22].encode("hex"),
                                                    data[22:42].encode("hex"),
                                                    data[42:48].encode("hex"),
                                                    data[48:54].encode("hex"),
                                                    data[54:56].encode("hex"))

                    logCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                      'Manager',
                                                      recipient='Logger',
                                                      action='debug',
                                                      data=log_str)
                    self.CFxHandle.submitCBT(logCBT)

                    if not self.CMConfig["on-demand_connection"]:
                        return
                    if len(data) < 16:
                        return
                    self.create_connection_req(data[2:], idle_peers)

                elif(self.pendingCBT[sourceCBT_uid].action ==
                     'LINK_TRIMMER'):
                    for key in self.CBTMappings[sourceCBT_uid]:
                        if(self.pendingCBT[key].action ==
                           'QUERY_PEER_LIST_RESP'):
                            peer_list = self.pendingCBT[key].data
                        elif(self.pendingCBT[key].action ==
                             'QUERY_IPOP_STATE_RESP'):
                            ipop_state = self.pendingCBT[key].data
                    self.__link_trimmer(peer_list, ipop_state)

                elif(self.pendingCBT[sourceCBT_uid].action ==
                     'ONDEMAND_CONNECTION'):
                    for key in self.CBTMappings[sourceCBT_uid]:
                        if(self.pendingCBT[key].action == 'RESOLVE_RESP'):
                            ip4 = self.pendingCBT[key].data
                    data = self.pendingCBT[sourceCBT_uid].data
                    self.ondemand_create_connection(data['uid'],
                                                    data['idle_peers'],
                                                    ip4,
                                                    data['send_req'])

        else:
            logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',
                                              recipient='Logger',
                                              action='error',
                                              data="BaseTopologyManager: CBT"
                                              " already exists in "
                                              "pendingCBT dictionary")
            self.CFxHandle.submitCBT(logCBT)

    # Create an On-Demand connection with an idle peer
    def ondemand_create_connection(self, uid, idle_peers, ip4, send_req):
        logCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',
                                          recipient='Logger',
                                          action='debug',
                                          data="idle peers {0}"
                                          .format(idle_peers))
        self.CFxHandle.submitCBT(logCBT)
        peer = idle_peers[uid]
        fpr_len = len(self.ipop_state["_fpr"])
        fpr = peer["data"][:fpr_len]
        cas = peer["data"][fpr_len + 1:]

        logCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                          'Manager',
                                          recipient='Logger',
                                          action='debug',
                                          data="Start mutual"
                                          " creating connection")
        self.CFxHandle.submitCBT(logCBT)

        if send_req:
            cbt_data = {
                "method": "send_msg",
                "overlay_id": 1,
                "uid": uid,
                "data": fpr
            }

            TincanCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                 'Manager',
                                                 recipient='TincanSender',
                                                 action='DO_SEND_MSG',
                                                 data=cbt_data)
            self.CFxHandle.submitCBT(TincanCBT)

        self.create_connection(peer["uid"], fpr, 1,
                               self.CMConfig["sec"], cas, ip4)

    # Create a TinCan link on request to send the packet
    # received by the controller

    def create_connection_req(self, data, idle_peers):
        version_ihl = struct.unpack('!B', data[54:55])
        version = version_ihl[0] >> 4
        if version == 4:
            s_addr = socket.inet_ntoa(data[66:70])
            d_addr = socket.inet_ntoa(data[70:74])
        elif version == 6:
            s_addr = socket.inet_ntop(socket.AF_INET6, data[62:78])
            d_addr = socket.inet_ntop(socket.AF_INET6, data[78:94])

            # At present, we do not handle ipv6 multicast
            if d_addr.startswith("ff02"):
                return

        uid = ipoplib.gen_uid(d_addr)

        try:
            msg = idle_peers[uid]
        except KeyError:
            logCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                              'Manager',
                                              recipient='Logger',
                                              action='error',
                                              data="Peer {0} is not "
                                              "logged in".format(d_addr))
            self.CFxHandle.submitCBT(logCBT)
            return

        logCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                          'Manager',
                                          recipient='Logger',
                                          action='debug',
                                          data="idle_peers[uid]"
                                          " --- {0}".format(msg))
        self.CFxHandle.submitCBT(logCBT)

        cbt_data = {
            'uid': uid,
            'idle_peers': idle_peers,
            'send_req': True
        }

        CBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',
                                       recipient='BaseTopologyManager',
                                       action='ONDEMAND_CONNECTION',
                                       data=cbt_data)
        self.CFxHandle.submitCBT(CBT)

    def create_connection(self, uid, data, nid, sec, cas, ip4):

        conn_dict = {'uid': uid, 'fpr': data, 'nid': nid,
                     'sec': sec, 'cas': cas}
        createLinkCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                 'Manager',
                                                 recipient='LinkManager',
                                                 action='CREATE_LINK',
                                                 data=conn_dict)
        self.CFxHandle.submitCBT(createLinkCBT)

        cbtdata = {
            "uid": uid,
            "ip4": ip4,
        }

        TincanCBT = self.CFxHandle.createCBT(initiator='BaseTopologyManager',
                                             recipient='TincanSender',
                                             action='DO_SET_REMOTE_IP',
                                             data=cbtdata)
        self.CFxHandle.submitCBT(TincanCBT)

    def check_collision(self, msg_type, uid, conn_stat):
        if msg_type == "con_req" and \
           conn_stat == "req_sent":
            if uid > self.ipop_state["_uid"]:
                trimCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                   'Manager',
                                                   recipient='LinkManager',
                                                   action='TRIM_LINK',
                                                   data=uid)
                self.CFxHandle.submitCBT(trimCBT)

                conn_stat_pop_CBT = self.CFxHandle.createCBT(initiator='Base'
                                                             'TopologyManager',
                                                             recipient='Moni'
                                                             'tor',
                                                             action='DELETE_'
                                                             'CONN_STAT',
                                                             data=uid)
                self.CFxHandle.submitCBT(conn_stat_pop_CBT)
            return False
        elif msg_type == "con_resp":
            conn_stat_CBT = self.CFxHandle.createCBT(initiator='Base'
                                                     'TopologyManager',
                                                     recipient='Monitor',
                                                     action='STORE_CONN_STAT',
                                                     data={'uid': uid,
                                                           'status':
                                                           "resp_recv"})
            self.CFxHandle.submitCBT(conn_stat_CBT)
            return False
        else:
            return True

    def __link_trimmer(self, peer_list, ipop_state):
        for k, v in peer_list.iteritems():
            # Trim TinCan link if the peer is offline
            if "fpr" in v and v["status"] == "offline":
                if v["last_time"] > self.CMConfig["link_trimmer_wait_time"]:

                    cbtdata = {
                        "method": "send_msg",
                        "overlay_id": 1,
                        "uid": k,
                        "data": "destroy" + ipop_state["_uid"]
                    }
                    TincanCBT = self.CFxHandle.createCBT(initiator='Base'
                                                         'TopologyManager',
                                                         recipient='Tincan'
                                                         'Sender',
                                                         action='DO_SEND_MSG',
                                                         data=cbtdata)
                    self.CFxHandle.submitCBT(TincanCBT)

                    trimCBT = self.CFxHandle.createCBT(initiator='Base'
                                                       'TopologyManager',
                                                       recipient='LinkManager',
                                                       action='TRIM_LINK',
                                                       data=k)
                    self.CFxHandle.submitCBT(trimCBT)

            # Trim TinCan link if the On Demand Inactive Timeout occurs
            if self.CMConfig["on-demand_connection"] \
                    and v["status"] == "online":
                if v["last_active"] + self.CMConfig["on-demand_inactive_timeout"] \
                        < time.time():
                    logCBT = self.CFxHandle.createCBT(initiator='Base'
                                                      'TopologyManager',
                                                      recipient='Logger',
                                                      action='debug',
                                                      data="Inactive,"
                                                      " trimming node:{0}"
                                                      .format(k) +
                                                      cbt.initiator)
                    self.CFxHandle.submitCBT(logCBT)

                    cbtdata = {
                        "method": "send_msg",
                        "overlay_id": 1,
                        "uid": k,
                        "data": "destroy" + ipop_state["_uid"]
                    }
                    TincanCBT = self.CFxHandle.createCBT(initiator='Base'
                                                         'TopologyManager',
                                                         recipient='Tincan'
                                                         'Sender',
                                                         action='DO_SEND_MSG',
                                                         data=cbtdata)
                    self.CFxHandle.submitCBT(TincanCBT)

                    trimCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                                       'Manager',
                                                       recipient='LinkManager',
                                                       action='TRIM_LINK',
                                                       data=k)
                    self.CFxHandle.submitCBT(trimCBT)

    def timer_method(self):
        selfCBT = self.CFxHandle.createCBT(initiator='BaseTopology'
                                           'Manager',
                                           recipient='BaseTopology'
                                           'Manager',
                                           action='LINK_TRIMMER',
                                           data="")
        self.CFxHandle.submitCBT(selfCBT)

    def terminate(self):
        pass

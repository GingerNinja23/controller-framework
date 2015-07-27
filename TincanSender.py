import ipoplib
from ControllerModule import ControllerModule


class TincanSender(ControllerModule):

    def __init__(self, sock_list, CFxHandle, paramDict):

        self.CFxHandle = CFxHandle
        self.CMConfig = paramDict
        self.sock = sock_list[0]
        self.sock_svr = sock_list[1]
        self.pendingCBT = {}

    def initialize(self):

        logCBT = self.CFxHandle.createCBT(initiator='TincanSender',
                                          recipient='Logger',
                                          action='info',
                                          data="TincanSender Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self, cbt):

        if(cbt.action == 'DO_CREATE_LINK'):

            uid = cbt.data.get('uid')
            fpr = cbt.data.get('fpr')
            nid = cbt.data.get('nid')
            sec = cbt.data.get('sec')
            cas = cbt.data.get('cas')
            ipoplib.do_create_link(self.sock, uid, fpr, nid, sec, cas)

        elif(cbt.action == 'DO_TRIM_LINK'):

            # cbt.data contains the UID of the peer
            ipoplib.do_trim_link(self.sock, cbt.data)

        elif(cbt.action == 'DO_GET_STATE'):

            ipoplib.do_get_state(self.sock)

        elif(cbt.action == 'DO_SEND_MSG'):

            method = cbt.data.get("method")
            overlay_id = cbt.data.get("overlay_id")
            uid = cbt.data.get("uid")
            data = cbt.data.get("data")
            ipoplib.do_send_msg(self.sock, method, overlay_id, uid, data)

        elif(cbt.action == 'DO_SET_REMOTE_IP'):

            ipoplib.do_set_remote_ip(self.CFxObject.sock,
                                     uid, ip4, gen_ip6(uid))

        elif(cbt.action == 'ECHO_REPLY'):
            m_type = cbt.data.get('m_type')
            dest_addr = cbt.data.get('dest_addr')
            dest_port = cbt.data.get('dest_port')
            ipoplib.make_remote_call(self.sock_svr, m_type=m_type,
                                     dest_addr=dest_addr, dest_port=dest_port,
                                     payload=None, type="echo_reply")

        else:
            logCBT = self.CFxHandle.createCBT(initiator='TincanSender',
                                              recipient='Logger',
                                              action='warning',
                                              data="TincanSender: Unrecognized"
                                              "CBT from " + cbt.initiator)
            self.CFxHandle.submitCBT(logCBT)

    def timer_method(self):
        pass

    def terminate(self):
        pass

import select
from threading import Thread
from ControllerModule import ControllerModule


class TincanListener(ControllerModule):

    def __init__(self, sock_list, CFxHandle, paramDict):

        super(TincanListener,self).__init__()
        self.CFxHandle = CFxHandle
        self.sock = sock_list[0]
        self.sock_svr = sock_list[1]
        self.sock_list = sock_list
        self.CMConfig = paramDict

    def initialize(self):

        self.TincanListenerThread = Thread(target=self.__tincan_listener)
        self.TincanListenerThread.setDaemon(True)
        self.TincanListenerThread.start()

        logCBT = self.CFxHandle.createCBT(initiator='TincanListener',
                                          recipient='Logger',
                                          action='info',
                                          data="TincanListener Loaded")
        self.CFxHandle.submitCBT(logCBT)

    def processCBT(self, cbt):
        pass

    def timer_method(self):
        pass

    def __tincan_listener(self):
        while(True):
            socks, _, _ = select.select(self.sock_list, [], [],
                                        self.CMConfig["socket_read_wait_time"])

            for sock in socks:
                if(sock == self.sock or sock == self.sock_svr):
                    sock_to_read = socks[0]
                    data, adr = sock_to_read.recvfrom(self.CMConfig["buf_size"])
                    cbt = self.CFxHandle.createCBT(initiator='TincanListener',
                                                   recipient='Tincan'
                                                   'Dispatcher',
                                                   action='TINCAN_PKT',
                                                   data=[data, adr])
                    self.CFxHandle.submitCBT(cbt)

    def terminate(self):
        pass

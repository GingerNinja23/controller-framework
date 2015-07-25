from threading import Thread
from ControllerModule import ControllerModule


class TincanListener(ControllerModule):

    def __init__(self, sock_list, CFxHandle, paramDict):

        self.CFxHandle = CFxHandle
        self.sock_list = sock_list
        self.CMConfig = paramDict
        self.pendingCBT = {}

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

            if(socks):
                sock_to_read = socks[0]
                data, addr = sock_to_read.recvfrom(self.CMConfig["buf_size"])
                cbt = self.CFxHandle.createCBT(initiator='TincanListener',
                                               recipient='TincanDispatcher',
                                               action='TINCAN_PKT',
                                               data=[data, addr])
                self.CFxHandle.submitCBT(cbt)

    def terminate(self):
        pass

from ipoplib import *
from ControllerModule import ControllerModule

class AddressMapper(ControllerModule):

    def __init__(self,CFxObject,CFxHandle,paramDict):

        self.CFxHandle = CFxHandle
        self.paramDict = paramDict
        self.pendingCBT = {}
        self.CFxObject = CFxObject

    def initialize(self):
        
        # logCBT = self.CFxHandle.createCBT(initiator='AddressMapper',recipient='Logger',\
        #                                   action='info',data="AddressMapper Loaded")
        # self.CFxHandle.submitCBT(logCBT)
        print "AddressMapper loaded"
        # For GroupVPN
        # Populating the uid_ip_table with all the IPv4 addresses
        # and the corresponding UIDs in the /16 subnet
        parts = self.CFxObject.CONFIG["ip4"].split(".")
        ip_prefix = parts[0] + "." + parts[1] + "."
        for i in range(0, 255):
            for j in range(0, 255):
                ip = ip_prefix + str(i) + "." + str(j)
                uid = gen_uid(ip)
                self.CFxObject.uid_ip_table[uid] = ip


    def processCBT(self,cbt):

        if(cbt.action == 'ADD_MAPPING'):

            try:
                # cbt.data is a dict with uid and ip keys
                self.CFxObject.uid_ip_table[cbt.data['uid']] = cbt.data['ip']
            except KeyError:

                logCBT = self.CFxHandle.createCBT(initiator='AddressMapper',recipient='Logger',\
                                                  action='warning',\
                                                  data="Invalid ADD_MAPPING Configuration")
                self.CFxHandle.submitCBT(logCBT)

        elif(cbt.action == 'DEL_MAPPING'):

            self.CFxObject.uid_ip_table.pop(cbt.data) # Remove mapping if it exists

        elif(cbt.action == 'RESOLVE'):

            # Modify the CBT with the response data and send it back
            cbt.action = 'RESOLVE_RESP'

            # If mapping exists, return IP else return None
            cbt.data = self.CFxObject.uid_ip_table.get(cbt.data)

            # Swap inititator and recipient
            cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator 

            self.CFxHandle.submitCBT(cbt)

        elif(cbt.action == 'REVERSE_RESOLVE'):

            # Modify the CBT with the response data and send it back
            cbt.action = 'REVERSE_RESOLVE_RESP'
            ip = cbt.data
            cbt.data = None
            # Iterate through all items in dict for reverse lookup
            for key,value in self.CFxObject.uid_ip_table.items():
                if(value==ip):
                    cbt.data = key
                    break

            # Swap inititator and recipient
            cbt.initiator,cbt.recipient = cbt.recipient,cbt.initiator

            self.CFxHandle.submitCBT(cbt)

        else:
            logCBT = self.CFxHandle.createCBT(initiator='AddressMapper',recipient='Logger',\
                                              action='warning',\
                                              data="AddressMapper: Invalid CBT received from "\
                                              +cbt.initiator)
            self.CFxHandle.submitCBT(logCBT)

    def timer_method(self):
        pass


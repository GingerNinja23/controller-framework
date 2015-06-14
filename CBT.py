import random

class CBT(object):

    def __init__(self,initiator='',recipient='',action='',data=''):

        self.uid = random.randint(1000,9999)
        self.initiator = initiator
        self.recipient = recipient
        self.action = action
        self.data = data


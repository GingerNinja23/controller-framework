from abc import ABCMeta, abstractmethod # Only Python 2.6 and above


# Defining an abstract class which the controller
# modules will implement
class ControllerModule(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def processCBT(self):
        pass

    @abstractmethod
    def timer_method(self):
    	pass

    	
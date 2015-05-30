from abc import ABCMeta, abstractmethod # Only Python 2.6 and above


# Defining an abstract class which the controller
# modules will implement
class ControllerModule:
    __metaclass__ = ABCMeta

    @abstractmethod
    def processCBT(self):
        pass

'''# Sample Controller Module 1
class ModuleA1(ControllerModule):

	def __init__(self,cfxObject,paramDict):
		self.cfxObject = cfxObject
		self.paramDict = paramDict

	 # Main processing loop
	def processCBT(self):
		while(True): # Polling approach
			cbt = self.cfxObject.getCBT() # 
			# Process the CBT here
			# Analyse CBT. If heavy, run it on another thread



# Sample Controller Module 2
class ModuleC3(ControllerModule):

	def __init__(self,cfxObject,paramDict):
		self.cfxObject = cfxObject
		self.paramDict = paramDict

	def processCBT(self): # Main processing loop
		while(True): # Polling approach
			cbt = self.cfxObject.getCBT() # 
			# Process the CBT here
			# Analyse CBT. If heavy, run it on another thread'''
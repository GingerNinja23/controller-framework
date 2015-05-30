from ControllerModule import ControllerModule
import time


# Sample Controller Module 1
# ControllerModule is an abstract class
class ModuleA1(ControllerModule):

	def __init__(self,cfxObject,paramDict):
		self.cfxObject = cfxObject
		self.paramDict = paramDict

	def processCBT(self): # Main processing loop
		print  "ModuleA1 Loaded\n"
		while(True): # Polling approach
			time.sleep(2)
			cbt = self.cfxObject.getCBT("ModuleA1") # 
			if(cbt):
				print "Module A1: CBT received " + str(cbt)+"\n"
				# Process the CBT here
				# Analyse CBT. If heavy, run it on another thread

				if cbt['data'].startswith("C3"): # If data starts with C3, ask ModuleC3 to strip "C3" first
					cbt['initiator'] = "ModuleA1"
					cbt['recipient'] = "ModuleC3"
					self.cfxObject.submitCBT(cbt) # Issue CBT to CFx with ModuleC3 as recipient
					print "ModuleA1: CBT sent to ModuleC3 by ModuleA1 for processing\n"
				else:
					cbt['data'] = cbt['data'].strip("A1")
					print "ModuleA1: Finished Processing the CBT from CFx\n"
## Leyend Functions
This repository contains the functions used in the LAP entries of the LAP repository.
Each file is one function used in at least 1 LAP entry.


`check\_tip\_and\_pick`

	**Objective**
		A function that will pick up a tip with the given pipette object.
    		If there is no tip in the tiprack(s) associated with the pipette, a new tip rack will be defined with the function `define\_tiprack`, and the dictionary position\_deck will be updated.

	**Tested systems**
		Opentrons OT-2
	
	**Requirements**
		* Error OutOfTipsError from the package opentrons
		* `define\_tiprack`function
	
	**Input**
	4 Inputs required:
		* _pipette\_used_ (class opentrons.protocol_api.instrument_context.InstrumentContext): For example P20 Single-Channel GEN2 on right mount object
		* _position\_deck_ (dictionary): Dictionary with deck positions as keys and labware/module object as the value.
                                  		  For example {1: Opentrons 96 Tip Rack 20 µL on 1, 2: Opentrons 96 Tip Rack 20 µL on 2, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None, 11: None}
		* _variables\_define\_tiprack_ (class): script class with attributes APINameTipR (name of the tiprack associated with right mount pipette) and APINameTipL (name of the tiprack associated with left mount pipette).
                                  			For example:
	                                  			class Example():
	                                  				def \_\_init\_\_ (self):
	                                  					self.APINameTipR = opentrons\_96\_tiprack\_20ul
	                                  					self.APINameTipL = opentrons\_96\_tiprack\_300ul
		* _protocol_ (opentrons.protocol\_api.protocol\_context.ProtocolContext)
	 
	**Output**
		* The dictionary position_deck will be updated to have the new tiprack
		* The provided pipette will pick up a tip
	
	**Summary of functioning**
		1. Pick a tip with the _pipette\_used_ category. If that raises an OutTipError, steps 2 and 3 will be performed. If not, it will exit the function
		2. Check if the _pipette\_used_ has any tiprack associated:
			_No tip racks associated_
				a. A space, if it is available, is designated to the new tiprack with  the function `define\_tiprack`
				b. Check with mount the pipette is and assign the starting tip of that pipette
			_Tip rack associated_
				a. Check if the user wants the tip racks to be replaced
					**No replacement tiprack**
						I. A tiprack is defined if there is a place, and the dictionary position_deck is updated to reflect that definition
					**Replace tiprack**
						I. Pause the run so the user can replace the empty tip rack
						II. Reset tip rack
		3. Pick a tip with the pipette_used

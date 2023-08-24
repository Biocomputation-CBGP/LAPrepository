'check_tip_and_pick'

	*Objective*
		A function that will pick up a tip with the given pipette object.
    If there is no tip in the tiprack(s) associated with the pipette, a new tip rack will be defined with the function define_tiprack and the dictionary position_deck will be updated.

	*Tested systems*
		Opentrons OT-2
	
	*Requirements*
		- Error OutOfTipsError from the package opentrons
		- define_tiprack function
	
	*Input*
	4 Inputs required:
		- __pipette_used__ (class opentrons.protocol_api.instrument_context.InstrumentContext): For example P20 Single-Channel GEN2 on right mount object
		- __position_deck__ (dictionary): Dictionary with deck positions as keys and labware/module object as the value.
                                  For example {1: Opentrons 96 Tip Rack 20 µL on 1, 2: Opentrons 96 Tip Rack 20 µL on 2, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None, 11: None}
		- __variables_define_tiprack__ (class): script class with attributes APINameTipR (name of the tiprack associated with right mount pipette) and APINameTipL (name of the tiprack associated with left mount pipette).
                                  			For example:
                                  			class Example():
                                  				def __init__ (self):
                                  					self.APINameTipR = opentrons_96_tiprack_20ul
                                  					self.APINameTipL = opentrons_96_tiprack_300ul
		- __protocol__ (opentrons.protocol_api.protocol_context.ProtocolContext)
	 
	*Output*
		- The dictionary position_deck will be updated to have the new tiprack
		- The provided pipette will pick up a tip
	
	*Summary of functioning*
		1. Pick up a tip with the pipette_used category. If that raises an OutTipError, steps 2 and 3 will be performed. If not, it will exit the function
		2. Check if the pipette_used has any tiprack associated:
			No tip racks associated
				a. A space, if it is available, is designated to the new tiprack with  the function define_tiprack
				b. Check with mount the pipette is and assign the starting tip of that pipette
			Tip rack associated
				a. Check if the user wants the tip racks to be replaced
					No replace tiprack
						I. A tiprack is defined if there is a place, and the dictionary position_deck is updated to reflect that definition
					Replace tiprack
						I. Pause the run so the user can replace the empty tip rack
						II. Reset tip rack
		3. Pick a tip with the pipette_used

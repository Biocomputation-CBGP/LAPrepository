def mixing_eppendorf_15 (location_tube, volume_tube, program_variables, user_variables, protocol):
	"""
	This is a function to perfrom an extensive mixing of every eppendorf which should be done before distributing the reactives along the final plates
	
	Mixing is one of the most crucial parts of this workflow and that is why theer is a function only for it
	
	This function will perform the mixing and will return warnings (in case that is needed) and the final pipette that has been used
	"""
	# This function is going to perform the mixing of the tubes in the coldblock (it is setted for the 1500ul eppendorf because the positions are done manually)
	mastermix_mixing_volume_theory = volume_tube / 3
	try:
		aSuitablePippet_mixing = optimal_pipette_use(mastermix_mixing_volume_theory, program_variables.pipR, program_variables.pipL)
		max_vol_pipette = aSuitablePippet_mixing.max_volume
		if max_vol_pipette < mastermix_mixing_volume_theory:
			volume_mixing = max_vol_pipette
		else:
			volume_mixing = mastermix_mixing_volume_theory
			pass
	except NotSuitablePipette: # If this happens it means that the the volume is too low to any of the pipettes
		if program_variables.pipR.min_volume < program_variables.pipL.min_volume:
			volume_mixing = program_variables.pipR.min_volume
			aSuitablePippet_mixing = program_variables.pipR
		else:
			volume_mixing = program_variables.pipL.min_volume
			aSuitablePippet_mixing = program_variables.pipL

	if aSuitablePippet_mixing.has_tip:
		pass
	else:
		if aSuitablePippet_mixing.mount == "right" and program_variables.pipL != None and program_variables.pipL.has_tip:
			program_variables.pipL.drop_tip()
		elif aSuitablePippet_mixing.mount == "left" and program_variables.pipR != None and program_variables.pipR.has_tip:
			program_variables.pipR.drop_tip()
		check_tip_and_pick (aSuitablePippet_mixing, program_variables.deckPositions, user_variables, protocol)
	
	# After calculating the mixing volume, choosing a pipette and picking up a tip we perform the mix
	positions_mixing = z_positions_mix(volume_mixing) # This is the part that is customized for the 1500uL eppendorfs
	
	# We are going to mix 7 times at different heighs of the tube
	aSuitablePippet_mixing.mix(7, volume_mixing, location_tube.bottom(z=positions_mixing[1])) 
	aSuitablePippet_mixing.mix(7, volume_mixing, location_tube.bottom(z=positions_mixing[0])) 
	aSuitablePippet_mixing.mix(7, volume_mixing, location_tube.bottom(z=positions_mixing[2]))
	
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)
	# Now we are going to aspirate and dispense 3 times at different heights to mix a little bit more the content of the tube
	for i in range(2):
		aSuitablePippet_mixing.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
		aSuitablePippet_mixing.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
	for i in range(2):
		aSuitablePippet_mixing.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
		aSuitablePippet_mixing.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
	aSuitablePippet_mixing.blow_out(location_tube.center())
	
	return aSuitablePippet_mixing
def mixing_eppendorf_15 (location_tube, volume_tube, volume_mixing, pipette, protocol):
	"""
	Function that will perform the mixing of a 1.5mL eppendorf tube iwth a given pipette

	The pipette shoudl have a tip to perform this mixing

	5 arguments are needed for this function
	"""
	# Check if the pipette has a tip
	if not pipette.has_tip:
		raise Exception(f"{pipette} has no tip attached to peform the function 'mixing_eppendorf_15'")

	# Check if the given pipette can aspirate/dispense the volume
	if pipette.min_volume > volume_mixing or pipette.max_volume < volume_mixing:
		raise Exception(f"Volume of mixing, {volume_mixing}uL, should be a value between the {pipette} minimum and maximum aspiration/dispense volume which are {pipette.min_volume}uL and {pipette.max_volume}uL, respectively")
	
	# Check the positions in which the mixing is going to be performed
	positions_mixing = z_positions_mix_15eppendorf (volume_tube) # This is the part that is customized for the 1500uL eppendorfs
	
	# Now we perform the mixing of the eppendorf tube
	# We are going to mix 7 times at different heighs of the tube
	for position in positions_mixing:
		pipette.mix(7, volume_mixing, location_tube.bottom(z = position)) 
	
	for i in range(3):
		pipette.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	for i in range(3):
		pipette.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	for i in range(3):
		pipette.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)

	# Now we are going to aspirate and dispense 3 times at different heights to mix a little bit more the content of the tube
	for i in range(2):
		pipette.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
		pipette.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
	for i in range(2):
		pipette.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
		pipette.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
	
	# Finally we blow out in the centre of the tube any rests that have been left in the tip
	pipette.blow_out(location_tube.center())
	
	return
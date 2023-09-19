def distribute_z_tracking_falcon15ml (pipette_used, vol_source, vol_distribute_well, pos_source, pos_final):
	"""
	Function that will distribute a volume to a a list of positions from a flacon of 15mL tracking the height of the falcon so the pipette does not get wet
	and have enough volume to aspirate

	The pipette needs to have a tip to perform this function

	This function needs 5 mandatory arguments to run and it returns the volume that the source tube ends up having
	"""

	# Check that there is enough volume to distribute that volume
	if vol_source < len(pos_final)*vol_distribute_well:
		raise Exception(f"Not enough volume in the source tube, {vol_source}uL, to distribute {vol_distribute_well}uL to {len(pos_final)} reactions")
	
	# Check that the pipette has a tip
	if not pipette_used.has_tip:
		raise Exception(f"No tip attached to distribute with {pipette_used}")

	start_position = 0
	while start_position + 1 < len(pos_final): # Go throught all the positions
		# Calculate how many reactions we can distribute aspirating from the same height
		number_pos_distr = calculate_max_reactions_constant_height_15mLfalcon (pos_source, vol_source, len(pos_final[start_position:]), vol_distribute_well)
		# Set the positions that th epipette is going to be distribute
		position_distribute = pos_final[start_position:start_position+number_pos_distr]
		pipette_used.distribute(vol_distribute_well, find_safe_15mLfalcon_height (vol_source, pos_source), position_distribute, new_tip = "never", disposal_volume = 0)
		# Update the volume of the tube
		vol_source -= number_pos_distr*vol_distribute_well
		# Update the start position of the final wells
		start_position += number_pos_distr
	return vol_source
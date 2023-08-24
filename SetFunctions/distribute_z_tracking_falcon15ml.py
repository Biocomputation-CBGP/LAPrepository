def distribute_z_tracking_falcon15ml (pipette_used, vol_source, vol_distribute_well, pos_source, pos_final):
	"""
	This function will distribute from a pos_source to pos_final (list) taking in account the height of aspiration of the 15mL falcon tube,
	this way the pipette will not get wet during the transfering of liquids
	
	This function is mainly design to distribute reactives to a plate making less pipette movements with the same pipette because the volume to distribute is the same
	"""
	
	while len(pos_final) != 0: # This will go on until there are no elements in the list pos_final (there are no more positions to transfer reactives to)
		# We are going to compare the height before and after aspirating
		if position_dispense_aspirate_falcon15ml(vol_source, pos_source).point == position_dispense_aspirate_falcon15ml((vol_source-(len(pos_final)*vol_distribute_well)), pos_source).point:
			# Heights are the same, so we are going to take the whole volume and distribute it
			pipette_used.distribute(vol_distribute_well, position_dispense_aspirate_falcon15ml(vol_source, pos_source), pos_final, new_tip = "never", disposal_volume = 0)
			vol_source -= vol_distribute_well*len(pos_final)
			pos_final = []
		
		else:
			# Heights are not the same so we are going to take the maximum, distribute it, change the height and then distribute the rest
			pos_final_original = pos_final
			for number_positions in range(1, len(pos_final_original)+1):
				vol_needed = vol_distribute_well*len(pos_final[:number_positions])
				if position_dispense_aspirate_falcon15ml (vol_source, pos_source) == position_dispense_aspirate_falcon15ml ((vol_source-vol_needed), pos_source):
					next
				else:
					pipette_used.distribute(vol_distribute_well, position_dispense_aspirate_falcon15ml(vol_source, pos_source), pos_final[:number_positions], new_tip = "never", disposal_volume = 0)
					# If you change the disposal volume you need to take it in account when you are calculating the number of tubes
					vol_source -= vol_distribute_well*len(pos_final[:number_positions])
					pos_final = pos_final[number_positions:]
					break
	return
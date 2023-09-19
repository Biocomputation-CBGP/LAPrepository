def tube_to_tube_transfer (vol_transfer_reaction, positions_source_tubes, reactions_source_tubes, positions_final_tubes, reactions_final_tubes, program_variables, user_variables, protocol):
	"""
	Function that will transfer from n-tubes to m-tubes a volume in relation with the reactions.

	As well, if the pipettes need to be changed to transfer the volume, they will be changed

	If there is a tip attached to the pipette or pipettes, it will be used but at the end it will be dropped
	"""

	# Make sure that we have as many reactions elements as position elements for both source and final
	if len(positions_source_tubes) != len(reactions_source_tubes):
		raise Exception("The length of the lists source tube positions and source tubes reactions should be the same")
	
	if len(positions_final_tubes) != len(reactions_final_tubes):
		raise Exception("The length of the lists final tube positions and final tubes reactions should be the same")
	
	# Initialize the source tube
	source_tubes = generator_positions (list(map(lambda x, y:[x,y], positions_source_tubes, reactions_source_tubes)))
	current_source_tube = next(source_tubes) # It will return a touple (position, reactions)

	# Make sure that the transfer can be done
	if sum(reactions_source_tubes) < sum(reactions_final_tubes):
		raise Exception(f"The source tubes have a total of {sum(reactions_source_tubes)} reactions and the final tubes need {sum(reactions_final_tubes)}, the transfer cannot be done")

	if not program_variables.pipL and not program_variables.pipR:
		raise Exception("There are no pipettes attached in the robot. At least 1 is needed to perform the function 'tube_to_tube_transfer'")

	pipette_use = None #Initial

	# Find out if the tipracks are the same for later purposes
	if user_variables.APINameTipR == user_variables.APINameTipL:
		tipracks_same = True
	else:
		tipracks_same = False

	for final_tube, reactions_tube in zip(positions_final_tubes, reactions_final_tubes): # Go through the destination tubes
		while reactions_tube > 0:
			# Calculate how much volume we need to pass from 1 tube to another
			if current_source_tube[1] >= reactions_tube: # The current source tube has enough volume
				volume_transfer = vol_transfer_reaction*reactions_tube
				current_source_tube[1] -= reactions_tube
				reactions_tube = 0
			else: # more than 1 tube is needed to transfer the required volume
				volume_transfer = vol_transfer_reaction*current_source_tube[1]
				reactions_tube -= current_source_tube[1]
				current_source_tube[1] = 0
			
			# We choose the pipette that will transfer it. It can change between one tube and another one, that is why we check if it is the same one
			optimal_pipette = give_me_optimal_pipette (volume_transfer, program_variables.pipR, program_variables.pipL)
			
			# Find out the tiprack associated to the optimal_pipette
			# Also the first tip in case this is the first time the pipette is used
			if optimal_pipette.mount == "right":
				tiprack = user_variables.APINameTipR
				first_tip = user_variables.startingTipPipR
			else:
				tiprack = user_variables.APINameTipL
				first_tip = user_variables.startingTipPipL

			# We find out if the optimal pipette has a tip and it is the same pipette as the last one
			if optimal_pipette == pipette_use:
				if pipette_use.has_tip == False:
					check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = first_tip, same_tiprack = tipracks_same)
			else: # The last pipette used and the current one are different
				if pipette_use == None and optimal_pipette.has_tip == False: # This will be the case at the beginning of this function
					check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = first_tip, same_tiprack = tipracks_same)
				elif pipette_use != None and pipette_use.has_tip: # The previously used pipette has a tip
					pipette_use.drop_tip()
					if not optimal_pipette.has_tip:
						check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = first_tip, same_tiprack = tipracks_same)
					
			# Establish the optimal pipette as the one that is going to be used
			pipette_use = optimal_pipette

			# Transfer volume
			pipette_use.transfer(float(volume_transfer), current_source_tube[0], final_tube, new_tip = "never")

			# In case the source tube has no volume, we go to the next one
			if current_source_tube[1] == 0:
				try:
					current_source_tube = next(source_tubes)
				except StopIteration: # This is meant for the last tube
					break # If there were a pass this would be an infinite while

		if reactions_tube > 0: # The function should not get out of the while loop without the value reactions_tube reaching out 0
			raise Exception ("Something went wrong in the function 'tube_to_tube_transfer'")	

	# After moving the volumes from the tubes to tubes we drop the tip
	if pipette_use.has_tip:
		pipette_use.drop_tip()
	
	return
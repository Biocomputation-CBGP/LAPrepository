def tube_to_tube_transfer (vol_transfer_reaction, positions_source_tubes, reactions_source_tubes, positions_final_tubes, reactions_final_tubes, program_variables, user_variables, protocol):
	index_source_tube = 0 # Initial
	if program_variables.pipL:
		pipette_use = program_variables.pipL #Initial
	else:
		pipette_use = program_variables.pipR
	for index_final_tube, final_tube in enumerate(positions_final_tubes):
		while reactions_final_tubes[index_final_tube] > 0:
			# calculate how much volume we need to pass from 1 tube to another
			if reactions_source_tubes[index_source_tube] >= reactions_final_tubes[index_final_tube]:
				volume_transfer = vol_transfer_reaction*reactions_final_tubes[index_final_tube]
				reactions_source_tubes[index_source_tube] -= reactions_final_tubes[index_final_tube]
				reactions_final_tubes[index_final_tube] = 0
			else:
				volume_transfer = vol_transfer_reaction*reactions_source_tubes[index_source_tube]
				reactions_source_tubes[index_source_tube] = 0
				reactions_final_tubes[index_final_tube] -= reactions_source_tubes[index_source_tube]
				
			# We choose the pipette that will transfer it
			optimal_pipette = optimal_pipette_use(volume_transfer, program_variables.pipR, program_variables.pipL)
			if optimal_pipette != pipette_use and pipette_use.has_tip:
				pipette_use.drop_tip()
				pipette_use = optimal_pipette
				check_tip_and_pick (pipette_use, program_variables.deckPositions, user_variables, protocol)
			elif optimal_pipette != pipette_use and pipette_use.has_tip == False:
				pipette_use = optimal_pipette
				check_tip_and_pick (pipette_use, program_variables.deckPositions, user_variables, protocol)
			elif optimal_pipette == pipette_use and pipette_use.has_tip:
				pass
			elif optimal_pipette == pipette_use and pipette_use.has_tip == False:
				check_tip_and_pick (pipette_use, program_variables.deckPositions, user_variables, protocol)
			
			# Transfer volume
			pipette_use.transfer(float(volume_transfer), positions_source_tubes[index_source_tube], final_tube, new_tip = "never")

			# Define the source tube
			if reactions_source_tubes[index_source_tube] == 0:
				index_source_tube += 1
	if pipette_use.has_tip:
		pipette_use.drop_tip()
	
	return
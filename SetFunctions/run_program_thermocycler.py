def run_program_thermocycler (tc_mod, program, lid_temperature, final_lid_state, final_block_state, volume_sample, protocol):
	"""
	Function that will read the csv file with the steps of the program and will perform it
	in the thermocycler
	the program is already the pd.DataFrame, because it has already been read and establish that the lid temperature is okay,
	it exists, etc, i.e., control error of the file
	"""
	
	# initialyze the state of the variable cycle that we will use to control if the step is a cycle or a step
	cycle = False
	
	# set the initail temperature of the lid
	tc_mod.set_lid_temperature(lid_temperature)
	for row in program.iterrows():
		# Check if it is a cycle or not, if it is a start of the end of it
		# This will work because we have already donde contorl of the values of this column which only can be -, Start or End
		if row[1]["Cycle Status"].lower() == "start":
			profile_termo =[{"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])}]
			cycle = True
			continue
		elif row[1]["Cycle Status"].lower() == "end":
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
			tc_mod.execute_profile(steps = profile_termo,
								   repetitions = int(row[1]["Number of Cycles"]),
								   block_max_volume = volume_sample)
			cycle = False
			continue
		
		# Now we know if we have to add a step to the cycle or do the step directly
		if cycle == True:
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
		elif cycle == False:
			tc_mod.set_block_temperature(row[1]["Temperature"],
										 hold_time_seconds = float(row[1]["Time (s)"]),
										 block_max_volume = volume_sample)
	# Now we are going to put the block at one temeprature/open lid if it is establish like that
	tc_mod.deactivate_lid()
	
	if final_lid_state:
		tc_mod.open_lid()
	
	if pd.isna(final_block_state) == False:
		tc_mod.set_block_temperature(final_block_state,
									 block_max_volume = volume_sample)
	else:
		tc_mod.deactivate_block()
	return

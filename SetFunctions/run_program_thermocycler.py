import pandas as pd
import numpy as np

def run_program_thermocycler (tc_mod, program, lid_temperature, volume_sample, protocol, final_lid_state = False, final_block_state = np.nan):
	"""
	Function that will read a table with the steps that the thermocycler should perform and other data needed to establish the steps in the thermocycler

	This function will take 5 mandatory arguments and 2 optional
	"""

	# Error check
	if not all(name in program.columns for name in ["Cycle Status", "Temperature", "Time (s)", "Number of Cycles"]):
		raise Exception("The columns 'Temperature', 'Cycle Status', 'Time (s)' and 'Number of Cycles' need to be in the given table to perform this function")

	# Initialyze the state of the variable cycle that we will use to control if the step is a cycle or a step
	cycle = False
	
	# Set the initial temperature of the lid
	tc_mod.set_lid_temperature(lid_temperature)
	for row in program.iterrows(): # Go through all the table
		# Check if it is a cycle or not, if it is a start of the end of it
		if row[1]["Cycle Status"].lower() == "start": # Start of a set of steps that are goingto be a cycle
			profile_termo =[{"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])}] # Add the step
			cycle = True
			continue # Go to next row
		elif row[1]["Cycle Status"].lower() == "end": # The cycle has end so it is performed 
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
			if type(row[1]["Number of Cycles"]) == str:
				raise Exception("A row where the value of the column 'Cycle Status' is End should have a number in the column 'Number of Cycles'")
			elif type(row[1]["Number of Cycles"]) == float:
				raise Exception("The value of 'Number of Cycles' needs to be an integer, it cannot be a float")
			tc_mod.execute_profile(steps = profile_termo,
								   repetitions = row[1]["Number of Cycles"],
								   block_max_volume = volume_sample)
			cycle = False
			continue # Go to next row
		elif row[1]["Cycle Status"].lower() == "-": # Either an isolated step or a step in a cycle
			pass
		else:
			raise Exception (f"The column 'Cycle Status' only accepts 3 values: Start, End or -")
		
		# Now we know if we have to add a step to the cycle or do the step directly
		if cycle == True:
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
		elif cycle == False:
			tc_mod.set_block_temperature(row[1]["Temperature"],
										 hold_time_seconds = float(row[1]["Time (s)"]),
										 block_max_volume = volume_sample)
	
	
	tc_mod.deactivate_lid()
	
	# Now we are going to put the block at one temeprature and open lid if it is establish like that
	if final_lid_state:
		tc_mod.open_lid()
	
	if not pd.isna(final_block_state):
		tc_mod.set_block_temperature(final_block_state,
									 block_max_volume = volume_sample)
	else:
		tc_mod.deactivate_block()
	
	return
def find_well_by_value (value, possible_labwares):
	"""
	This labware should have the map of the labwares where the value should be looked for and the position where that labware is
	
	This function will only return the first well with that value
	
	If it doesnt find the value in the labware it will return None
	"""
	for possible_labware in possible_labwares.values():
		cell_pd_value = possible_labware["Map Names"][possible_labware["Map Names"].isin([value])].stack().index # stack() returns a pandas.Series in which the indexes are the (row, column) of the cells that the value is
		if len(cell_pd_value) == 0:
			continue
		if len(cell_pd_value) > 1:
			raise Exception(f"The DNA Part {value} is in the labware {possible_labware['Label']} more than once")
		else:
			well_value = str(cell_pd_value[0][0])+str(cell_pd_value[0][1])
			return possible_labware["Opentrons Place"][well_value]
	raise Exception(f"{value} is not in the provied Maps")
def find_well_by_value (value, possible_labwares):
	"""
	Function that will read a table of names and a table of positions and will return a list of the well(s) in the labware that
	the value given correspond in the maps (tables)

	The function needs 2 arguments to work
	"""
	wells_value = []

	for possible_labware in possible_labwares.values(): # Go through the given labwares
		cell_pd_value = possible_labware["Map Names"][possible_labware["Map Names"].isin([value])].stack().index # stack() returns a pandas.Series in which the indexes are the (row, column) of the cells that the value is True
		
		if len(cell_pd_value) == 0: # The value is not in this map, go to the next one
			continue
		
		for well in cell_pd_value: # Go through all the cells that have value
			well_value = str(well[0])+str(well[1])
			# See if that cell actually exists in the labware
			try:
				wells_value.append(possible_labware["Opentrons Place"][well_value])
			except KeyError:
				raise Exception(f"The value '{value}' has been found in the map cell '{well_value}' but that well does not exist in the labware {possible_labware['Opentrons Place']}")
	
	if len(wells_value) == 0:
		raise Exception(f"The value '{value}' cannot be found in the provied possible_labwares")
	
	return wells_value

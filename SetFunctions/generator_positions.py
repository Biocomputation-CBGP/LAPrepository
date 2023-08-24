def generator_positions (labware_wells_name):
	"""
	Generator of the positions to transfer, it will give you the next element of a list every time it is called
	"""
	for well in labware_wells_name:
		yield well
def setting_labware (number_labware, labware_name, positions, protocol, label = None):
	"""
	In this function we will set how many labwares we need of every category (source labwares, final, coldblocks, falcon tube racks, etc)
	
	This function will only set the labwares in the different slots of the deck, with not calculate how many we need,
	this way we do not have to change this function and only change the setting_labware function from protocol to protocol
	"""
	position_plates = [position for position, labware in positions.items() if labware == None] # We obtain the positions in which there are not labwares
	all_plates = {}

	for i in range (number_labware):
		labware_set = False # Control variable
		for position in position_plates:
			try:
				if label == None:
					plate = protocol.load_labware(labware_name, position)
				elif type(label) == str:
					plate = protocol.load_labware(labware_name, position, label = f"{label} {i+1} Slot {position}")
				elif type(label) == list:
					plate = protocol.load_labware(labware_name, position, label = f"{label[i]} Slot {position}")
				all_plates[position] = plate
				labware_set = True
				break # It has set the labware so we can break from the loop of positions
			except DeckConflictError:
				continue
		
		# Control to see if the labware has been able to load in some free space. This will be tested after trying all the positions
		if labware_set:
			position_plates.remove(position) # We take from the lits the value that has been used or the last
		else:
			raise Exception(f"Not all {labware_name} have been able to be placed, try less samples or another combination of variables")

	return all_plates
def vol_pipette_matcher (volumes_distribute, positions_distribute, pip_r, pip_l):
	"""
	Function that taking 2 pipettes and a list of volumes it established which volume should be transfered with
	which pipette. All of those volumes are matched with a location

	4 arguments are needed for the function. The arguments that correspond to pip_r and pip_l can be None, but
	if both of them are None an exception will be raised
	"""
	
	# Initiate the variables that are going to be returned
	vol_r = []
	pos_r = []
	vol_l = []
	pos_l = []

	# Error control
	if not pip_r and not pip_l:
		raise Exception("There are no pipettes attached to perform the function 'vol_pipette_matcher'")

	if len (volumes_distribute) != len (positions_distribute):
		raise Exception("The lists representing the positions and volumes to distribute need to be of equal length")

	# Go through all the volumes to define which pipette should transfer it
	for volume_transfer, position in zip (volumes_distribute, positions_distribute):
		# No pipette is needed to transfer that volume
		if volume_transfer == 0:
			continue
		
		selected_pipette = give_me_optimal_pipette (volume_transfer, pip_l, pip_r)

		if selected_pipette.mount == "right":
			vol_r.append(volume_transfer)
			pos_r.append(position)
		else:
			vol_l.append(volume_transfer)
			pos_l.append(position)

	return vol_r, pos_r, vol_l, pos_l
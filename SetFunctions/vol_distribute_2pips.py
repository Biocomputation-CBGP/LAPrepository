def vol_distribute_2pips (volumes_distribute, positions_distribute, pip_r, pip_l):
	vol_r = []
	pos_r = []
	vol_l = []
	pos_l = []
	for index_position, volume_transfer in enumerate(volumes_distribute):
		if volume_transfer == 0:
			continue
		
		selected_pipette = optimal_pipette_use(volume_transfer, pip_l, pip_r)
		if selected_pipette.mount == "right":
			vol_r.append(volume_transfer)
			pos_r.append(positions_distribute[index_position])
		else:
			vol_l.append(volume_transfer)
			pos_l.append(positions_distribute[index_position])
	return vol_r, pos_r, vol_l, pos_l
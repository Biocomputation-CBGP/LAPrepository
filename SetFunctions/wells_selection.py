def wells_selection (list_wells, number_samples_take, type_selection):
	if type_selection == "first":
		return list_wells[:number_samples_take]
	elif type_selection == "random":
		return random.sample(list_wells, number_samples_take)
	elif type_selection == "last":
		return list(reversed(list_wells))[:number_samples_take]
	else:
		raise Exception(f"Type of selection {type_selection} not contempleted yet. Only options are first, last and random")
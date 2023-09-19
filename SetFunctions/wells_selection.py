import random

def wells_selection (list_wells, number_samples_take, type_selection):
	"""
	Function that will select in a specific way elements from a given list

	The elements will be selected from the beginning, the end or randomly from the list

	This function needs 3 arguments
	"""
	
	# Error control
	if number_samples_take > len(list_wells):
		raise Exception(f"The number of elements to select, {number_samples_take}, is greater than the length of the input list, {len(list_wells)}")
	
	# Depending on the argument given, a type of selection is done
	if type_selection == "first":
		return list_wells[:number_samples_take]
	elif type_selection == "random":
		return random.sample(list_wells, number_samples_take)
	elif type_selection == "last":
		return list(reversed(list_wells))[:number_samples_take]
	else:
		raise Exception(f"Type of selection {type_selection} not contempleted yet. Only options are 'first', 'last' and 'random'")
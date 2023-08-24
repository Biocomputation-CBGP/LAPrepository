def generate_combinations_dict (pd_combination):
	combination_dict = {}
	list_names = list(pd_combination["Name"].values)
	for name_combination in list_names:
		elements_row = [element for element in pd_combination.loc[pd_combination["Name"] == name_combination].values[0][1:] if not pd.isna(element)]
		combination_dict[name_combination] = {"acceptor":elements_row[0], "modules":elements_row[1:]}
	return combination_dict
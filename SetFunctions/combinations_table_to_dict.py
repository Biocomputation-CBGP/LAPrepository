import pandas as pd

def combinations_table_to_dict (table, column_key, column_isolated, name_key_col_isolated = "isolatedCol", name_key_rest_columns = "restCol"):
	"""
	Function that will take a table and turn it into a dictionary in which 1 column will be the key of the items and the values will be another dictionary.
	In that items value will have 2 items, one that is going to be the value sof one column and another one that will be the values of the rest of the columns

	It will return something similar to {column_key_value:{name_key_col_isolated:column_isolated_value, name_key_rest_columns:[value_col1, value_col2, ...]}, ...}
	
	This function needs 3 mandatory arguments and 2 optional
	"""
	# Error control
	if column_key not in table.columns:
		raise Exception(f"The column {column_key}, the one that will give the key value of the items, does not exist in the pandas dataframe provided")
	if column_isolated not in table.columns:
		raise Exception(f"The column {column_isolated}, which will be 1 of the elements of the items, does not exist in the pandas dataframe provided")
	
	if table[column_key].duplicated().any():
		raise Exception(f"The column {column_key} of the dataframe needs to have unique values, it cannot have duplicated values")
	
	combination_dict = {} # Initial
	list_keys = list(table[column_key].values)

	for name_row in list_keys: # Go through all the rows of the given table
		# Set the value of the name and the isolated column
		combination_dict[name_row] = {name_key_col_isolated: table.loc[table[column_key] == name_row, column_isolated].values[0], name_key_rest_columns:[]}
		row_name = table[table[column_key] == name_row]
		combination_dict[name_row][name_key_rest_columns] = [element for element in row_name.loc[:,~row_name.columns.isin([column_key,column_isolated])].values[0] if not pd.isna(element)]
	return combination_dict
"""
Python script destined to OT-2
This script performs a merge of samples from N source plates to a lower amount of final plates
This script needs an excel file attached to perform the running
For more info go to https://github.com/Biocomputation-CBGP/LAPrepository/tree/main/LAPEntries and/or
https://github.com/Biocomputation-CBGP/OT2/tree/main/GoldenStandardAssembly
"""

## Packages needed for the running of the protocol
import opentrons
import pandas as pd
import math
import random
import numpy as np
from opentrons.motion_planning.deck_conflict import DeckConflictError #in version 6.3.1
from opentrons.protocol_api.labware import OutOfTipsError # in version 6.3.1


class UserVariables:
	def __init__(self, general, each_plate, pipettes, reagents, modules, combinations, profile = None):
		# General Variables Sheet
		self.numberSourcePlates = general[general["Variable Names"] == "Number DNA Parts Plates"]["Value"].values[0] # It is equivalent to the other protocols source plates
		self.APINameFinalPlate = general[general["Variable Names"] == "API Name Final Plate"]["Value"].values[0]
		self.APINameEppendorfPlate = general[general["Variable Names"] == "API Name Labware Eppendorfs Reagents"]["Value"].values[0]
		self.finalMapName = general[general["Variable Names"] == "Name File Final Constructs"]["Value"].values[0]
		self.wellStartFinalPlate = general[general["Variable Names"] == "Well Start Final Labware"]["Value"].values[0]
		self.APINameSamplePlate = general[general["Variable Names"] == "API Name Labware DNA Constructs"]["Value"].values[0] # It is equivalent to the other protocols source plates

		# Module Variables sheet
		self.presenceHS = modules[modules["Variable Names"] == "Presence Heater-Shaker"]["Value"].values[0]
		self.presenceTermo = modules[modules["Variable Names"] == "Presence Thermocycler"]["Value"].values[0]
		self.finalStateLid = modules[modules["Variable Names"] == "Final Open Lid"]["Value"].values[0]
		self.temperatureLid = modules[modules["Variable Names"] == "Temperature Lid"]["Value"].values[0]
		self.finalTemperatureBlock = modules[modules["Variable Names"] == "Hold Block Temperature After Profile"]["Value"].values[0]
		self.rpm = modules[modules["Variable Names"] == "RPM Heater-Shaker"]["Value"].values[0]
		self.APINameLabwareHS = modules[modules["Variable Names"] == "API Name Heater-Shaker Labware"]["Value"].values[0]
		self.pause = modules[modules["Variable Names"] == "Pause Before Temperature Program"]["Value"].values[0]
		self.initialTemperatureBlock = modules[modules["Variable Names"] == "Initial Thermocycle Block Temperature"]["Value"].values[0]

		# Reaction Variables Sheet
		self.acceptorVolume = reagents[reagents["Variable Names"] == "Volume Acceptor Plasmid (uL)"]["Value"].values[0]
		self.moduleVolume = reagents[reagents["Variable Names"] == "Volume Module Plasmid (uL)"]["Value"].values[0]
		self.restrictionEnzymeVolume = reagents[reagents["Variable Names"] == "Volume Restriction Enzyme (uL)"]["Value"].values[0]
		self.ligaseVolume = reagents[reagents["Variable Names"] == "Volume Ligase (uL)"]["Value"].values[0]
		self.bufferVolume = reagents[reagents["Variable Names"] == "Volume Buffer (uL)"]["Value"].values[0]
		self.serumVolume = reagents[reagents["Variable Names"] == "Volume ATP/Serum (uL)"]["Value"].values[0]
		self.extraPipettingFactor = reagents[reagents["Variable Names"] == "Extra Pipetting Factor"]["Value"].values[0]
		self.finalVolume = reagents[reagents["Variable Names"] == "Volume Final Each Reaction (uL)"]["Value"].values[0]

		# Pipette Variables Sheet
		self.APINamePipL = pipettes[pipettes["Variable Names"] == "API Name Left Pipette"]["Value"].values[0]
		self.APINamePipR = pipettes[pipettes["Variable Names"] == "API Name Right Pipette"]["Value"].values[0]
		self.startingTipPipR = pipettes[pipettes["Variable Names"] == "Initial Tip Right Pipette"]["Value"].values[0]
		self.startingTipPipL = pipettes[pipettes["Variable Names"] == "Initial Tip Left Pipette"]["Value"].values[0]
		self.APINameTipR = pipettes[pipettes["Variable Names"] == "API Name Tiprack Right Pipette"]["Value"].values[0]
		self.APINameTipL = pipettes[pipettes["Variable Names"] == "API Name Tiprack Left Pipette"]["Value"].values[0]
		self.replaceTiprack = pipettes[pipettes["Variable Names"] == "Replace Tipracks"]["Value"].values[0]

		# Temperature profile, in case it needs it
		if isinstance(profile, pd.DataFrame):
			self.temperatureProfile = profile.dropna(how="all")
		else:
			self.temperatureProfile = None

		# Per Plate Variables Sheet
		self.samplesPerPlate = list(each_plate[each_plate["Variable Names"] == "Number of Parts"].values[0][1:]) # Equivalent to Number of Samples
		self.nameSheetMapParts = list(each_plate[each_plate["Variable Names"] == "Name Map DNA Parts"].values[0][1:])
		
		# Combinations Sheet
		self.combinations_dataframe = combinations.dropna(how="all")

		return
	
	def check(self, protocol):
		"""
		Function that will check the variables of the Template and will raise errors that will crash the OT run
		It is a validation function of the variables checking errors or inconsistencies
	
		This function is dependant again with the variabels that we have, some checks are interchangable between protocols, but some of them are specific of the variables
		"""
		
		labware_context = opentrons.protocol_api.labware
		
		# First thing that we are going to check is that the minimum variables are present:
		if pd.isna([self.APINameFinalPlate, self.APINameEppendorfPlate, self.finalMapName, self.wellStartFinalPlate, self.APINameSamplePlate, self.numberSourcePlates]).any():
			raise Exception("None of the variables in the Sheet 'GeneralVariables' can be empty")
		if pd.isna([self.presenceHS, self.presenceTermo]).any():
			raise Exception("The variables 'Presence Thermocycler' and 'Presence Heater-Shaker' in the Sheet 'ModuleVariables' cannot be empty")
		if pd.isna([self.acceptorVolume, self.moduleVolume, self.restrictionEnzymeVolume,self.ligaseVolume,self.bufferVolume,self.serumVolume,self.extraPipettingFactor,self.finalVolume]).any():
			raise Exception("None of the variables in the Sheet 'ReactionVariables' can be empty")
		if pd.isna(self.replaceTiprack):
			raise Exception("The variable 'Replace Tipracks' in the Sheet 'PipetteVariables' cannot be empty")
		
		# Check that there is at least 1 pipette to perform the protocol
		if pd.isna(self.APINamePipL) and pd.isna(self.APINamePipR):
			raise Exception("At least 1 pipette is needed to perform this protocol")
		
		# Check that if the pipette is not empty, neither the tiprack or the initial pipette should not be empty
		if not pd.isna(self.APINamePipL) and (pd.isna(self.startingTipPipL) or pd.isna(self.APINameTipL)):
			raise Exception("If the variable 'API Name Left Pipette' has a value, both 'API Name Tiprack Left Pipette' and 'Initial Tip Left Pipette' need to be filled")
		if pd.isna(self.APINamePipL):
			self.startingTipPipL = None
			self.APINameTipL = None
		
		if not pd.isna(self.APINamePipR) and (pd.isna(self.startingTipPipR) or pd.isna(self.APINameTipR)):
			raise Exception("If the variable 'API Name Right Pipette' has a value, both 'API Name Tiprack Right Pipette' and 'Initial Tip Right Pipette' need to be filled")
		if pd.isna(self.APINamePipR):
			self.startingTipPipR = None
			self.APINameTipR = None
		
		# Check that if the tipracks are the same, the initial tips should be ethe same as well
		if not pd.isna(self.APINamePipL) and not pd.isna(self.APINamePipR):
			if self.APINameTipL == self.APINameTipR:
				if self.startingTipPipL != self.startingTipPipR:
					raise Exception("If the tipracks of the right and left mount pipettes are the same, the initial tip should be as well.")
		
		# Check all the boolean values and set them
		if str(self.presenceHS).lower() == "true":
			self.presenceHS = True
		elif str(self.presenceHS).lower() == "false":
			self.presenceHS = False
		else:
			raise Exception ("The variable 'Presence Heater-Shaker' only accepts 2 values, True or False")
		
		if self.presenceHS:
			if pd.isna(self.APINameLabwareHS) or pd.isna(self.rpm):
				raise Exception("If heater-shaker is present there are 2 variables which cannot be left empty: 'RPM Heater-Shaker' and 'API Name Heater-Shaker Labware'")
		
		if str(self.replaceTiprack).lower() == "true":
			self.replaceTiprack = True
		elif str(self.replaceTiprack).lower() == "false":
			self.replaceTiprack = False
		else:
			raise Exception ("The variable 'Replace Tipracks' only accepts 2 values, True or False")
		
		if str(self.presenceTermo).lower() == "true":
			self.presenceTermo = True
		elif str(self.presenceTermo).lower() == "false":
			self.presenceTermo = False
		else:
			raise Exception ("The variable 'Presence Thermocycler' only accepts 2 values, True or False")
		
		if self.presenceTermo:
			if pd.isna(self.finalStateLid) or pd.isna(self.pause)  or pd.isna(self.temperatureLid):
				raise Exception("If thermocycler is present there are 3 variables which cannot be left empty: 'Final Open Lid', 'Temperature Lid' and 'Pause Before Temperature Program'")
		
			if str(self.finalStateLid).lower() == "true":
				self.finalStateLid = True
			elif str(self.finalStateLid).lower() == "false":
				self.finalStateLid = False
			else:
				raise Exception ("The variable 'Final Open Lid' only accepts 2 values, True or False meaning at the end of the themnorcycler steps the lid will be open or close, respectivelly")

			if str(self.pause).lower() == "true":
				self.pause = True
			elif str(self.pause).lower() == "false":
				self.pause = False
			else:
				raise Exception ("The variable 'Pause Before Temperature Program' only accepts 2 values, True or False")
			
			if not isinstance(self.temperatureProfile, pd.DataFrame):
				raise Exception ("We do not have the Sheet 'TemperatureProfile' but we have the variable 'Presence of Thermocycler' set as True, that is incompatible")
			else: # Let's check the values of the temperature profile dataframe are correct
				# First check that it has the appropiate columns
				if not all(item in self.temperatureProfile.columns for item in ["Temperature", "Time (s)", "Number of Cycles", "Cycle Status"]):
					raise Exception('4 columns are needed in the TemperatureProfile sheet: "Temperature", "Time (s)", "Number of Cycles" and "Cycle Status"')
				for row in self.temperatureProfile.iterrows():
					# Let's check that no cells are left empty
					if any(pd.isna(element) for element in row[1].values):
						raise Exception("In a row in the sheet TemperatureProfile none of the cells can have an empty value")
					# Check that the cycles status have any of the possible values
					if row[1]["Cycle Status"].lower() not in ["start","end","-"]:
						raise Exception("One step of the profile has another value for 'Cycle Status' that is neither 'Start', 'End' nor '-'")
					if pd.isna(row[1]["Time (s)"]) or type(row[1]["Time (s)"]) not in [float, int]:
						raise Exception("The time of each step in the temperature profile need to be filled and with a number")
					if pd.isna(row[1]["Number of Cycles"]) or not (row[1]["Number of Cycles"] == "-" or type(row[1]["Number of Cycles"]) == int):
						raise Exception("The number of cycles for each step in the temperature profile cannot be left empty, it has to be a hyphen or a integer")
					if row[1]["Cycle Status"].lower() == "end" and type(row[1]["Number of Cycles"]) != int:
						raise Exception("In the rows where the value for 'Cycle Status' is End, the value of the column 'Number of Cycles' needs to be a integer")
					if pd.isna(row[1]["Temperature"]) or type(row[1]["Temperature"]) not in [float, int]:
						raise Exception("The temperature of each step in the temperature profile need to be filled and with a number")
					# Not we check that the temperatures are between the ranges
					if row[1]["Temperature"] > 110 or row[1]["Temperature"] < 4:
						raise Exception("One step of the profile cannot be set with the thermocycler, the operative range of the thermocycler is 4-99C")
					
			if self.temperatureLid > 110 or self.temperatureLid < 37:
				raise Exception("Lid temperature cannot be set with the thermocycler, the operative range of the thermocycler is 37-110C")
			
			if pd.isna(self.finalTemperatureBlock) == False and (self.finalTemperatureBlock > 99 or self.finalTemperatureBlock < 4):
				raise Exception("Hold Block temperature cannot be set with the thermocycler, the operative range of the thermocycler is 4-99C")
			
			if pd.isna(self.initialTemperatureBlock) == False and (self.initialTemperatureBlock > 99 or self.initialTemperatureBlock < 4):
				raise Exception("Initial Block Temperature cannot be set with the thermocycler, the operative range of the thermocycler is 4-99C")
			
		else:
			self.finalStateLid = None
			self.pause = None
			self.finalTemperatureBlock = None
			self.temperatureLid = None
			self.initialTemperatureBlock = None
		
		try:
			definition_source_plate = labware_context.get_labware_definition(self.APINameSamplePlate)
			definition_final_plate = labware_context.get_labware_definition(self.APINameFinalPlate)
			definition_rack = labware_context.get_labware_definition(self.APINameEppendorfPlate)
			if pd.isna(self.APINamePipR) == False:
				definition_tiprack_right = labware_context.get_labware_definition(self.APINameTipR)
			if pd.isna(self.APINamePipL) == False:
				definition_tiprack_left = labware_context.get_labware_definition(self.APINameTipL)
			if self.presenceHS:
				definition_HS = labware_context.get_labware_definition(self.APINameLabwareHS)
		except OSError: # This would be catching the FileNotFoundError that happens when a labware is not found
			raise Exception("One or more of the introduced labwares or tipracks are not in the labware directory of the opentrons. Check for any typo of the api labware name.")
		
		# We need at least 1 source plate
		if self.numberSourcePlates < 1:
			raise Exception("We need at least 1 Number DNA Parts Plates to perform the protocol")

		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if len(self.samplesPerPlate) < (self.numberSourcePlates) or len(self.nameSheetMapParts) < (self.numberSourcePlates):
			raise Exception("We need to have at least the same number of plate columns on the Sheet 'SamplesPlateVariables' as in 'Number DNA Parts Plates'")
		if any(pd.isna(elem) == True for elem in self.samplesPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.samplesPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Number of Parts' need to be as many as the 'Number DNA Parts Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.nameSheetMapParts[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.nameSheetMapParts[self.numberSourcePlates:]):
			raise Exception("The values of 'Name Map DNA Parts' need to be as many as the 'Number DNA Parts Plates' and be in consecutive columns")
		
		# Check if there is any typo in the starting tip of both pipettes
		if pd.isna(self.APINamePipR) == False and (self.startingTipPipR not in definition_tiprack_right["groups"][0]["wells"]):
			raise Exception("Starting tip of right pipette is not valid, check for typos")
		if pd.isna(self.APINamePipL) == False and (self.startingTipPipL not in definition_tiprack_left["groups"][0]["wells"]):
			raise Exception("Starting tip of left pipette is not valid, check for typos")
		
		# Check if there is a typo in the first destination well
		if self.wellStartFinalPlate not in definition_final_plate["groups"][0]["wells"]:
			raise Exception(f"The variable 'Well Start Final Labware' {self.wellStartFinalPlate} does not exist in {self.APINameFinalPlate}")
		
		# Check all the sheets that are stated in the 'Per Plate Variables' exist and it follows exactly the same names as the labware set in 'API Name Labware DNA Constructs'
		all_elements_maps = [] # This is meant for the next check which will see if the values are only once in the maps
		for index_map, name_map in enumerate(self.nameSheetMapParts[:self.numberSourcePlates]):
			try:
				map_content = pd.read_excel('/data/user_storage/VariablesMoCloAssembly.xlsx', sheet_name = name_map, index_col=0, engine = "openpyxl")
				# map_content = pd.read_excel('VariablesMoCloAssembly.xlsx', sheet_name = name_map, index_col=0, engine = "openpyxl")
			except ValueError: # Error that appears when the sheet 'name_map' does not exist in the excel file
				raise Exception(f"The Sheet '{name_map}' does not exist in the file 'VariablesMoCloAssembly.xlsx'")
			
			# If the number of parts can actually fit the labware
			if self.samplesPerPlate[index_map] > len(definition_source_plate["wells"]):
				raise Exception(f"One of the values of 'Number of Parts' exceeds the number of wells in the labware '{self.APINameSamplePlate}'")


			# If exists we will check it has same number of rows and columns at least, when labware is load we will check the names
			map_rows, map_columns = map_content.shape
			if map_rows != len(definition_source_plate["ordering"][0]) or map_columns != len(definition_source_plate["ordering"]):
				raise Exception(f"The Sheet '{name_map}' needs to have the same columns and rows as the labware '{self.APINameSamplePlate}'. If there is no part in a position, leave cell empty.\nThe name of the rows and columns should be included in the sheet.")
			
			# Check that the number of values correspond to the one set in the variables
			number_nan = map_content.isna().sum().sum()
			if map_content.size - number_nan != self.samplesPerPlate[index_map]:
				raise Exception(f"Map '{name_map}' has {map_content.size - number_nan} values filled but in variable 'Number of Parts' the value is {self.samplesPerPlate[index_map]}, check for inconsistencies")
			# If exist and the dimensions are the same as the labware we add the values to our all_elements_maps list to check after
			all_elements_maps += map_content.values.tolist()
		
		# We are going to check now if there is some repeated element in the map(s) of dna input
		# This check has to be after checking the Excel Sheet Maps exist
		# We unflat the the values of the maps and take out the nan elements
		unflat_values = [element for sublist in all_elements_maps for element in sublist if not pd.isna(element)]
		
		if pd.Series(unflat_values).is_unique == False:
			raise Exception("There is at least 1 element that is repeteated along the DNA Parts Maps and this protocol can only handle 1 tube per DNA part")
		
		# Check that the Names columns are not empty
		if self.combinations_dataframe["Name"].isna().any():
			raise Exception("The values of the column 'Name' cannot be left empty")
		
		# Check that the acceptor plasmid column is not empty
		if self.combinations_dataframe["Acceptor Plasmid"].isna().any():
			raise Exception("The values of the column 'Acceptor Plasmid' cannot be left empty")

		# Check if any combination list name is repeated
		if pd.Series(self.combinations_dataframe["Name"].values).is_unique == False:
			raise Exception("Names on the Combinations Sheet have to be unique")
		
		# Check that there is no value on the map that is not being used
		all_values_combinations = np.concatenate(self.combinations_dataframe.iloc[:,1:].values).tolist()
		for element in unflat_values:
			if element not in all_values_combinations:
				raise Exception(f"The DNA part '{element}' is not used in any combination. Take it out of the map and run again")

		# Check if the thermocycler is included if we need more than 1 final plate
		if self.presenceTermo and len(self.combinations_dataframe["Name"].values) > len(definition_final_plate["wells"].keys()):
			raise Exception("If the Thermocycler is present, only 1 final plate can be created and all of your combinations does not fit in the selected final labware")			
		
		# Check that all the reactives are actually numbers
		if any(type(reactive) == str for reactive in [self.acceptorVolume, self.restrictionEnzymeVolume, self.ligaseVolume, self.bufferVolume, self.serumVolume, self.finalVolume, self.extraPipettingFactor, self.moduleVolume]):
			raise Exception("All of the values in the sheet 'ReactionVariables' should not be strings, all of them must be numbers")

		# Check that the factor is between 0 an 1
		if self.extraPipettingFactor >= 1 or self.extraPipettingFactor < 0:
			raise Exception("The variable 'Extra Pipetteing Factor' should be in range [0, 1)")

		# Check if the sum of the common reactives are greater than the final volume
		# The check of common reactives + parts <= final volume is going to be done when the water volumes are calculated
		if self.acceptorVolume + self.restrictionEnzymeVolume + self.ligaseVolume + self.bufferVolume + self.serumVolume > self.finalVolume:
			raise Exception("The sum of the common reactives (ligase, buffer, RE, serum) + acceptor plasmid is greater than the final volume established")
		
		# Check that the final volume of the reaction is not greater than the max volume of the final well (s)
		first_key = list(labware_context.get_labware_definition(self.APINameFinalPlate)["wells"].keys())[0]
		vol_max_well = labware_context.get_labware_definition(self.APINameFinalPlate)["wells"][first_key]["totalLiquidVolume"]
		if self.finalVolume > vol_max_well:
			return(f"The final volume exceeds the max volume of the wells in the labware {self.APINameFinalPlate}")
		
		return
	
class SettedParameters:
	def __init__(self, deck_positions):
		self.pipR = None
		self.pipL = None
		self.sameTipRack = None
		self.samplePlates = {}
		self.finalPlates = {}
		self.reactiveWells = {}
		self.mixWells = {"Reactions Per Tube":[], "Volumes":[], "Definition Liquid": None}
		self.deckPositions = {key: None for key in range(1,deck_positions)}
		self.volREFactor = 0
		self.volLigaseFactor = 0
		self.volBufferFactor = 0
		self.volSerumFactor = 0
		self.volTotal = 0
		self.volTotalFactor = 0
		self.tc_mod = None
		self.hs_mods = {}
		self.combinations = None
		self.sumSamples = 0 # Initialize 
		self.colors_mediums = ["#93c47d", "#f44336", "#a7aef9", "#c27ba0","#d4f1f9", "#d3cfcf"] # RE, ligase, buffer, serum, water, mix --> We will add the acceptors and modules later
		
		return
	
	def assign_variables(self, user_variables, protocol):
		# Source Plates Definition, in this case, the DNA Plate definitions
		for index_plate in range(user_variables.numberSourcePlates):
			# We wil fill this maps after setting the labware
			self.samplePlates[index_plate] = {"Position":None,
											  "Label":f"DNA Plate '{user_variables.nameSheetMapParts[index_plate]}'",
											  "Opentrons Place":None,
											  "Map Names":None,
											  "Map Volumes":None,
											  "Map Liquid Definitions":None}

		self.combinations = combinations_table_to_dict (user_variables.combinations_dataframe, "Name", "Acceptor Plasmid", name_key_col_isolated = "acceptor", name_key_rest_columns = "modules")
		self.sumSamples = len(self.combinations)
		
		# Final Plate Variables
		# Lets find first how many final plates do we need
		number_wells_final_plate = len(opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["wells"])
		number_final_needed = math.ceil((opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)+self.sumSamples)/number_wells_final_plate)
		for index_final_plate in range(number_final_needed):
			self.finalPlates[index_final_plate] = {"Position":None,
											"Label":f"Combination Plate {index_final_plate+1}",
											"Opentrons Place":None,
											"Map Combinations":None # We will create this map when we establish the final plate
											}
		
		self.reactiveWells =  {
			"RE":{"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples,
			"Definition Liquid": protocol.define_liquid(name = "Restriction Enzyme", description = "Enzyme that will cut the acceptor plasmid and module parts",display_color = "#93c47d")},
			"Ligase":{"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples,
			"Definition Liquid": protocol.define_liquid(name = "Ligase",description = "Ligase Enzyme",display_color = "#f44336")},
			"Buffer":{"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples,
			"Definition Liquid": protocol.define_liquid(name = "Buffer",description = "Ligase Buffer",display_color = "#a7aef9")},
			"Serum":{"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples,
			"Definition Liquid": protocol.define_liquid(name = "Serum/ATP",description = "Serum or ATP needed for the reaction to be preformed",display_color = "#c27ba0")},
			"Water":{"Positions":[], "Volumes":None, "Volumes Per Tube":None, "Number Total Reactions":self.sumSamples,
			"Definition Liquid": protocol.define_liquid(name = "Water", description = "Water that will fill the volume of each well until final volume", display_color = "#d4f1f9")}
		}
		
		self.volREFactor = user_variables.restrictionEnzymeVolume*(1+user_variables.extraPipettingFactor)
		self.volLigaseFactor = user_variables.ligaseVolume*(1+user_variables.extraPipettingFactor)
		self.volBufferFactor = user_variables.bufferVolume*(1+user_variables.extraPipettingFactor)
		self.volSerumFactor = user_variables.serumVolume*(1+user_variables.extraPipettingFactor)
		self.volTotal = user_variables.restrictionEnzymeVolume+user_variables.ligaseVolume+user_variables.bufferVolume+user_variables.serumVolume
		self.volTotalFactor = self.volTotal*(1+user_variables.extraPipettingFactor)
		
		# Pipette Variables
		if pd.isna(user_variables.APINamePipL) == False:
			self.pipL = protocol.load_instrument(user_variables.APINamePipL, mount = "left")
		else:
			# Establish all the variables set to the left pipette as none
			user_variables.APINameTipL = None
			user_variables.startingTipPipL = None
			
		if pd.isna(user_variables.APINamePipR) == False:
			self.pipR = protocol.load_instrument(user_variables.APINamePipR, mount = "right")
		else:
			# Establish all the variables set to the right pipette as none
			user_variables.APINameTipR = None
			user_variables.startingTipPipR = None
		
		if user_variables.APINameTipR == user_variables.APINameTipL:
			self.sameTipRack = True
		else:
			self.sameTipRack = False

		if user_variables.presenceTermo:
			self.tc_mod = protocol.load_module("thermocycler")
			self.tc_mod.open_lid()
			self.deckPositions = {**self.deckPositions, **{7:"Thermocycler",8:"Thermocycler",10:"Thermocycler",11:"Thermocycler"}}

		return
	
class MapLabware:
	def __init__(self, labware):

		self.name_rows = list(labware.rows_by_name().keys())
		self.name_columns = list(labware.columns_by_name().keys())
		number_rows = len(self.name_rows)
		number_columns = len(self.name_columns)
		
		self.map = pd.DataFrame(np.full((number_rows,number_columns),None),columns=self.name_columns,index=self.name_rows)
		self.map.index.name = "Row/Column"

	def assign_value(self, value, row, column):
		self.map.loc[row, column] = value
	
	def export_map(self, name_final_file):
		self.map.to_csv("/data/user_storage/"+name_final_file, header = True, index = True)
		# self.map.to_csv(name_final_file, header = True, index = True)
		
class NotSuitablePipette(Exception):
	"Custom Error raised when there is no pipette that can transfer the volume"
	def __init__(self, value):
		message = f"Not a suitable pipette to aspirate/dispense {value}uL"
		super().__init__(message)
	pass

# Functions definitions
# ----------------------------------
# ----------------------------------

def setting_labware (number_labware, labware_name, positions, protocol, module = False, label = None):
	"""
	In this function we will set how many labwares we need of every category (source labwares, final, coldblocks, falcon tube racks, etc)
	
	4 mandatory arguments and 2 optional 
	"""
	position_plates = [position for position, labware in positions.items() if labware == None] # We obtain the positions in which there are not labwares
	all_plates = {}
	if type(label) == list and len(label) != number_labware:
		raise Exception("If the argument 'label' is a list as many names should be provided as the argument 'number_labware'")

	for i in range (number_labware):
		labware_set = False # Control variable
		for position in position_plates:
			try:
				if not module: # Meaning that we are going to load labwares
					if label == None:
						plate = protocol.load_labware(labware_name, position)
					elif type(label) == str:
						plate = protocol.load_labware(labware_name, position, label = f"{label} {i+1} Slot {position}")
					elif type(label) == list:
						plate = protocol.load_labware(labware_name, position, label = f"{label[i]} Slot {position}")
				else: # We are going to load modules
					if label == None:
						plate = protocol.load_module(labware_name, position)
					elif type(label) == str:
						plate = protocol.load_module(labware_name, position, label = f"{label} {i+1} Slot {position}")
					elif type(label) == list:
						plate = protocol.load_module(labware_name, position, label = f"{label[i]} Slot {position}")
				# If it reaches this point the labware as been set
				all_plates[position] = plate
				labware_set = True
				break # It has set the labware so we can break from the loop of positions
			except DeckConflictError:
				continue
			except ValueError: # This will be raised when a thermocycler is tried to set in a position where it cannot be and if the position does not exist
				continue
		
		# Control to see if the labware has been able to load in some free space. This will be tested after trying all the positions
		if labware_set:
			position_plates.remove(position) # We take from the list the value that has been used or the last
		else:
			raise Exception(f"Not all {labware_name} have been able to be placed, try less samples or another combination of variables")

	return all_plates

def number_tubes_needed (vol_reactive_per_reaction_factor, number_reactions, vol_max_tube):
	"""
	Function that will return the number of tubes that is needed for a given number of reactions

	3 mandatory arguments are needed for this function to work
	"""

	# Set initial values
	number_tubes = 1
	reactions_per_tube = [number_reactions]
	volumes_tubes = [vol_reactive_per_reaction_factor*number_reactions]*number_tubes
	
	# Check if it can be done
	if vol_reactive_per_reaction_factor > vol_max_tube:
		raise Exception(f"The volume of each reaction, {vol_reactive_per_reaction_factor}uL, is greater than the max volume of the tube, {vol_max_tube}uL")

	while any(volume > vol_max_tube for volume in volumes_tubes): # If there is some volume that is greater than the max volume we are going to enter in the loop
		number_tubes += 1 # We add one tube so the volume can fit in the tubes
		
		# Now we redistribute the reactions (and volume) to the tubes so it will be the most homogeneus way
		reactions_per_tube = [int(number_reactions/number_tubes)]*number_tubes
		tubes_to_add_reaction = number_reactions%number_tubes # This is the remainder of the division #reactions / #tubes so it can never be greater than #tubes
		
		for i in range(tubes_to_add_reaction): # We will add 1 reaction to every tube until there are no more reaction remainders
			reactions_per_tube[i] += 1
		# Adding one will make the volume of the tubes more homogeneous

		# Calculate the new volumes
		volumes_tubes = [vol_reactive_per_reaction_factor*number_reactions_tube for number_reactions_tube in reactions_per_tube]
	
	# When the volume can fit every tube (exit from the while loop) we return the number of tubes and the reactions that will fit in every tube
	return (number_tubes, reactions_per_tube, volumes_tubes)

def generator_positions (labware_wells_name):
	"""
	Function that will return the next element everytime is called from a given list
	"""
	for well in labware_wells_name:
		yield well

def check_tip_and_pick (pipette_used, tiprack, position_deck, protocol, replace_tiprack = False, initial_tip = "A1", same_tiprack = False):
	"""
	Function that will pick a tip and if there is not a tip available it will define a new tip rack and pick one in case it is possible to establish
	a new tip rack.
	For that purpose it will need 7 arguments, 3 optional (replace_tiprack, initial_tip, same_tiprack) and 4 mandatory (pipette_used, tiprack, position_deck, protocol)
	"""
	try:
		pipette_used.pick_up_tip()
		# When there are no tips left in the tiprack OT will raise an error
	except OutOfTipsError:
		if len(pipette_used.tip_racks) == 0: # There are no tip racks attached to the pipette
			# If it is possible a tiprack will be established
			position_deck = {**position_deck , **define_tiprack (pipette_used, tiprack, position_deck, protocol, same_tiprack = same_tiprack)}
			
			# We establish now the starting tip, it will only be with the first addition, the rest will be establish that the first tip is in A1 directly
			if same_tiprack and "right" in protocol.loaded_instruments.keys() and "left" in protocol.loaded_instruments.keys(): # Same tipracks
				protocol.loaded_instruments["right"].starting_tip = pipette_used.tip_racks[0][initial_tip]
				protocol.loaded_instruments["left"].starting_tip = pipette_used.tip_racks[0][initial_tip]
			else: # Different tipracks
				protocol.loaded_instruments[pipette_used.mount].starting_tip = pipette_used.tip_racks[0][initial_tip]
			
		else:# There is already a tiprack attached to the pipette 
			if replace_tiprack == False: # A tip rack will be added to the layout in case it is possible
				position_deck = {**position_deck , **define_tiprack (pipette_used, tiprack, position_deck, protocol, same_tiprack = same_tiprack)}
			else: # The tip rack will be replaced by the one already placed
				# Careful with this part if you are traspassing this script into jupyter because this will crash your jupyter (will wait until resume and it does not exist)
				protocol.pause("Replace Empty Tiprack With A Full One And Press Resume In OT-App")
				if same_tiprack and "right" in protocol.loaded_instruments.keys() and "left" in protocol.loaded_instruments.keys():
					protocol.loaded_instruments["right"].reset_tipracks()
					protocol.loaded_instruments["left"].reset_tipracks()
				else:
					pipette_used.reset_tipracks()
		
		#Finally, we pick up the needed tip        
		pipette_used.pick_up_tip()
	
	return
	
def define_tiprack (pipette, tiprack_name, position_deck, protocol, same_tiprack = False):
	"""
	Function that will define, if possible, a tip rack in the first position free that does not raise a deck conflict
	and assigned it to the pipette.

	In case that the right and left pipette have the same tiprack, menaing the same_tiprack variable is set as True,
	the tip rack will be assigned to both pipettes

	This function needs 4 mandatory arguments and 1 optional
	"""

	# First we find out how many positions are available
	positions_free = [position for position, labware in position_deck.items() if labware == None]
	
	if len(positions_free) == 0:
		raise Exception("There is not enough space in the deck for the tip rack needed")
	
	for position in positions_free: # Loop in case there is a position that has deck conflicts but it can still be placed in another one
		
		try:
			tiprack = protocol.load_labware(tiprack_name, position)
			position_deck[position] = tiprack_name
		except OSError:
			raise Exception (f"The tip rack '{tiprack_name}' is not found in the opentrons namespace, check for typos or add it to the custom labware")
		except DeckConflictError: # Continue to the next position
			continue
		
		# Attach the tip rack to the right pipette(s)
		if same_tiprack and "right" in protocol.loaded_instruments.keys() and "left" in protocol.loaded_instruments.keys():# Both tip racks are the same
			protocol.loaded_instruments["right"].tip_racks.append(tiprack)
			protocol.loaded_instruments["left"].tip_racks.append(tiprack)
		else:
			protocol.loaded_instruments[pipette.mount].tip_racks.append(tiprack)
		
		# If it has reached this point it means that the tiprack has been defined
		return {position:tiprack_name}
	
	# If it has reached this point it means that the tip rack has not been able to be defined
	raise Exception(f"Due to deck conflicts, the tiprack '{tiprack_name}' has not been able to be placed. Try another combination of variables")


def give_me_optimal_pipette (aVolume, pipette_r = None, pipette_l = None):
	"""
	Function that given a set of pipettes  will return the one more that will transfer the volume with less movements

	This function requires 1 mandatory argument and 2 optional
	"""

	if pipette_r == None and pipette_l == None: # No pipettes attached
		raise Exception(f"There is not a pippette attached to aspirate/dispense {aVolume}uL")
	
	# Look if one of them is the only option
	elif pipette_r == None and aVolume >= pipette_l.min_volume: # One mount is free, only need that the volume is more than the min of the pipette
		return pipette_l
	
	elif pipette_l == None and aVolume >= pipette_r.min_volume:
		return pipette_r
	
	# Now we look if there are 2 and the most apropiate should be returned
	elif pipette_r != None and pipette_l != None:
		# Define if both of the pipettes can take the volume
		if aVolume >= pipette_l.min_volume and aVolume >= pipette_r.min_volume:
			if pipette_l.min_volume >= pipette_r.min_volume:
				return pipette_l
			else:
				return pipette_r
		# Not both of them can pick it, so it is a matter to figure out if 1 of them can do it
		elif aVolume >= pipette_l.min_volume:
			return pipette_l
		elif aVolume >= pipette_r.min_volume:
			return pipette_r
		else: # None of the pipettes can hold that volume
			raise NotSuitablePipette(aVolume)
	
	else: # This will be the case if there is 1 pipette attached but it can take the volume
		raise NotSuitablePipette(aVolume)

def run_program_thermocycler (tc_mod, program, lid_temperature, volume_sample, protocol, final_lid_state = False, final_block_state = np.nan):
	"""
	Function that will read a table with the steps that the thermocycler should perform and other data needed to establish the steps in the thermocycler

	This function will take 5 mandatory arguments and 2 optional
	"""

	# Error check
	if not all(name in program.columns for name in ["Cycle Status", "Temperature", "Time (s)", "Number of Cycles"]):
		raise Exception("The columns 'Temperature', 'Cycle Status', 'Time (s)' and 'Number of Cycles' need to be in the given table to perform this function")

	# Initialyze the state of the variable cycle that we will use to control if the step is a cycle or a step
	cycle = False
	
	# Set the initial temperature of the lid
	tc_mod.set_lid_temperature(lid_temperature)
	for row in program.iterrows(): # Go through all the table
		# Check if it is a cycle or not, if it is a start of the end of it
		if row[1]["Cycle Status"].lower() == "start": # Start of a set of steps that are goingto be a cycle
			profile_termo =[{"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])}] # Add the step
			cycle = True
			continue # Go to next row
		elif row[1]["Cycle Status"].lower() == "end": # The cycle has end so it is performed 
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
			if type(row[1]["Number of Cycles"]) == str:
				raise Exception("A row where the value of the column 'Cycle Status' is End should have a number in the column 'Number of Cycles'")
			elif type(row[1]["Number of Cycles"]) == float:
				raise Exception("The value of 'Number of Cycles' needs to be an integer, it cannot be a float")
			tc_mod.execute_profile(steps = profile_termo,
								   repetitions = row[1]["Number of Cycles"],
								   block_max_volume = volume_sample)
			cycle = False
			continue # Go to next row
		elif row[1]["Cycle Status"].lower() == "-": # Either an isolated step or a step in a cycle
			pass
		else:
			raise Exception (f"The column 'Cycle Status' only accepts 3 values: Start, End or -")
		
		# Now we know if we have to add a step to the cycle or do the step directly
		if cycle == True:
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
		elif cycle == False:
			tc_mod.set_block_temperature(row[1]["Temperature"],
										 hold_time_seconds = float(row[1]["Time (s)"]),
										 block_max_volume = volume_sample)
	
	
	tc_mod.deactivate_lid()
	
	# Now we are going to put the block at one temeprature and open lid if it is establish like that
	if final_lid_state:
		tc_mod.open_lid()
	
	if not pd.isna(final_block_state):
		tc_mod.set_block_temperature(final_block_state,
									 block_max_volume = volume_sample)
	else:
		tc_mod.deactivate_block()
	
	return

def z_positions_mix_15eppendorf (vol_mixing):
	"""
	Function that will define the positions of mixing according to the volume of each eppendorf tube
	
	These heights have been manually measured for 1.5mL eppendorfs to attach z to aproximatelly the volume associated
	
	We will have 3 mixing heights at the end, but not neccessarilly different within each other
	"""
	
	# Establish the manual measured z height
	position_bottom = 1
	position_100 = 6
	position_100_250 = 9
	position_250 = 11
	position_500 = 16
	position_750 = 20
	position_1000 = 25
	position_1250 = 30
	
	#Assigned to the volume the 3 positions [min, center, max] that we are going to use in the mixing process
	if vol_mixing <= 100: # The values of comparing are volumes (in uL)
		return [position_bottom, position_bottom, position_bottom]
	elif vol_mixing > 100 and vol_mixing <= 250:
		return [position_bottom, position_100, position_100_250]
	elif vol_mixing > 250 and vol_mixing <= 500:
		return [position_bottom, position_100, position_250]
	elif vol_mixing > 500 and vol_mixing <= 750:
		return [position_100, position_250, position_500]
	elif vol_mixing > 750 and vol_mixing <= 1000:
		return [position_100, position_250, position_750]
	elif vol_mixing > 1000 and vol_mixing <= 1250:
		return [position_100, position_500, position_1000]
	elif vol_mixing > 1250:
		return [position_100, position_500, position_1250]

def mixing_eppendorf_15 (location_tube, volume_tube, volume_mixing, pipette, protocol):
	"""
	Function that will perform the mixing of a 1.5mL eppendorf tube iwth a given pipette

	The pipette shoudl have a tip to perform this mixing

	5 arguments are needed for this function
	"""
	# Check if the pipette has a tip
	if not pipette.has_tip:
		raise Exception(f"{pipette} has no tip attached to peform the function 'mixing_eppendorf_15'")

	# Check if the given pipette can aspirate/dispense the volume
	if pipette.min_volume > volume_mixing or pipette.max_volume < volume_mixing:
		raise Exception(f"Volume of mixing, {volume_mixing}uL, should be a value between the {pipette} minimum and maximum aspiration/dispense volume which are {pipette.min_volume}uL and {pipette.max_volume}uL, respectively")
	
	# Check the positions in which the mixing is going to be performed
	positions_mixing = z_positions_mix_15eppendorf (volume_tube) # This is the part that is customized for the 1500uL eppendorfs
	
	# Now we perform the mixing of the eppendorf tube
	# We are going to mix 7 times at different heighs of the tube
	for position in positions_mixing:
		pipette.mix(7, volume_mixing, location_tube.bottom(z = position)) 
	
	for i in range(3):
		pipette.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	for i in range(3):
		pipette.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	for i in range(3):
		pipette.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)

	# Now we are going to aspirate and dispense 3 times at different heights to mix a little bit more the content of the tube
	for i in range(2):
		pipette.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
		pipette.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
	for i in range(2):
		pipette.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
		pipette.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
	
	# Finally we blow out in the centre of the tube any rests that have been left in the tip
	pipette.blow_out(location_tube.center())
	
	return

def tube_to_tube_transfer (vol_transfer_reaction, positions_source_tubes, reactions_source_tubes, positions_final_tubes, reactions_final_tubes, program_variables, user_variables, protocol):
	"""
	Function that will transfer from n-tubes to m-tubes a volume in relation with the reactions.

	As well, if the pipettes need to be changed to transfer the volume, they will be changed

	If there is a tip attached to the pipette or pipettes, it will be used but at the end it will be dropped
	"""

	# Make sure that we have as many reactions elements as position elements for both source and final
	if len(positions_source_tubes) != len(reactions_source_tubes):
		raise Exception("The length of the lists source tube positions and source tubes reactions should be the same")
	
	if len(positions_final_tubes) != len(reactions_final_tubes):
		raise Exception("The length of the lists final tube positions and final tubes reactions should be the same")
	
	# Initialize the source tube
	source_tubes = generator_positions (list(map(lambda x, y:[x,y], positions_source_tubes, reactions_source_tubes)))
	current_source_tube = next(source_tubes) # It will return a touple (position, reactions)

	# Make sure that the transfer can be done
	if sum(reactions_source_tubes) < sum(reactions_final_tubes):
		raise Exception(f"The source tubes have a total of {sum(reactions_source_tubes)} reactions and the final tubes need {sum(reactions_final_tubes)}, the transfer cannot be done")

	if not program_variables.pipL and not program_variables.pipR:
		raise Exception("There are no pipettes attached in the robot. At least 1 is needed to perform the function 'tube_to_tube_transfer'")

	pipette_use = None #Initial

	# Find out if the tipracks are the same for later purposes
	if user_variables.APINameTipR == user_variables.APINameTipL:
		tipracks_same = True
	else:
		tipracks_same = False

	for final_tube, reactions_tube in zip(positions_final_tubes, reactions_final_tubes): # Go through the destination tubes
		while reactions_tube > 0:
			# Calculate how much volume we need to pass from 1 tube to another
			if current_source_tube[1] >= reactions_tube: # The current source tube has enough volume
				volume_transfer = vol_transfer_reaction*reactions_tube
				current_source_tube[1] -= reactions_tube
				reactions_tube = 0
			else: # more than 1 tube is needed to transfer the required volume
				volume_transfer = vol_transfer_reaction*current_source_tube[1]
				reactions_tube -= current_source_tube[1]
				current_source_tube[1] = 0
			
			# We choose the pipette that will transfer it. It can change between one tube and another one, that is why we check if it is the same one
			optimal_pipette = give_me_optimal_pipette (volume_transfer, program_variables.pipR, program_variables.pipL)
			
			# Find out the tiprack associated to the optimal_pipette
			# Also the first tip in case this is the first time the pipette is used
			if optimal_pipette.mount == "right":
				tiprack = user_variables.APINameTipR
				first_tip = user_variables.startingTipPipR
			else:
				tiprack = user_variables.APINameTipL
				first_tip = user_variables.startingTipPipL

			# We find out if the optimal pipette has a tip and it is the same pipette as the last one
			if optimal_pipette == pipette_use:
				if pipette_use.has_tip == False:
					check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = first_tip, same_tiprack = tipracks_same)
			else: # The last pipette used and the current one are different
				if pipette_use == None and optimal_pipette.has_tip == False: # This will be the case at the beginning of this function
					check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = first_tip, same_tiprack = tipracks_same)
				elif pipette_use != None and pipette_use.has_tip: # The previously used pipette has a tip
					pipette_use.drop_tip()
					if not optimal_pipette.has_tip:
						check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = first_tip, same_tiprack = tipracks_same)
					
			# Establish the optimal pipette as the one that is going to be used
			pipette_use = optimal_pipette

			# Transfer volume
			pipette_use.transfer(float(volume_transfer), current_source_tube[0], final_tube, new_tip = "never")

			# In case the source tube has no volume, we go to the next one
			if current_source_tube[1] == 0:
				try:
					current_source_tube = next(source_tubes)
				except StopIteration: # This is meant for the last tube
					break # If there were a pass this would be an infinite while

		if reactions_tube > 0: # The function should not get out of the while loop without the value reactions_tube reaching out 0
			raise Exception ("Something went wrong in the function 'tube_to_tube_transfer'")	

	# After moving the volumes from the tubes to tubes we drop the tip
	if pipette_use.has_tip:
		pipette_use.drop_tip()
	
	return

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

# Body of the Program
# ----------------------------------
# ----------------------------------
metadata = {
'apiLevel':'2.14'
}

def run(protocol:opentrons.protocol_api.ProtocolContext):
	labware_context = opentrons.protocol_api.labware
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Read Variables Excel, define the user and protocol variables and check them for initial errors
	# Read Excel
	excel_variables = pd.read_excel("/data/user_storage/VariablesMoCloAssembly.xlsx", sheet_name = None, engine = "openpyxl")
	# excel_variables = pd.read_excel("VariablesMoCloAssembly.xlsx", sheet_name = None, engine = "openpyxl")
	# Let's check that the minimal sheets
	name_sheets = list(excel_variables.keys())

	if not all(item in name_sheets for item in ["GeneralVariables","PerPlateVariables","PipetteVariables","ModuleVariables","ReactionVariables", "Combinations"]):
		raise Exception('The Excel file needs to have min the sheets "GeneralVariables","PerPlateVariables","PipetteVariables","ModuleVariables","ReactionVariables" and "Combinations"\nThey must have those names')
	
	# Check that all variables needed in each variables
	general_variables = excel_variables.get("GeneralVariables")
	reagents_variables = excel_variables.get("ReactionVariables")
	plate_variables = excel_variables.get("PerPlateVariables")
	pip_variables = excel_variables.get("PipetteVariables")
	module_variables = excel_variables.get("ModuleVariables")
	combinations_variables = excel_variables.get("Combinations")
	
	if not all(item in list(general_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'GeneralVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in general_variables["Variable Names"].values for item in ['API Name Final Plate', 'API Name Labware Eppendorfs Reagents', 'Name File Final Constructs', 'Well Start Final Labware', 'API Name Labware DNA Constructs', 'Number DNA Parts Plates']):
			raise Exception("'GeneralVariables' sheet table needs to have 6 rows with the following names: 'API Name Final Plate', 'API Name Labware Eppendorfs Reagents', 'Name File Final Constructs', 'Well Start Final Labware', 'API Name Labware DNA Constructs', 'Number DNA Parts Plates'")
		
	if not all(item in list(reagents_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'ReactionVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in reagents_variables["Variable Names"].values for item in ['Volume Acceptor Plasmid (uL)', 'Volume Module Plasmid (uL)', 'Volume Restriction Enzyme (uL)', 'Volume Ligase (uL)', 'Volume Buffer (uL)', 'Volume ATP/Serum (uL)', 'Volume Final Each Reaction (uL)', 'Extra Pipetting Factor']):
			raise Exception("'ReactionVariables' sheet table needs to have 8 rows with the following names: 'Volume Acceptor Plasmid (uL)', 'Volume Module Plasmid (uL)', 'Volume Restriction Enzyme (uL)', 'Volume Ligase (uL)', 'Volume Buffer (uL)', 'Volume ATP/Serum (uL)', 'Volume Final Each Reaction (uL)', 'Extra Pipetting Factor'")
	
	if not all(item in list(plate_variables.columns) for item in ["Variable Names"]):
		raise Exception("'PerPlateVariables' sheet table needs to have at least 1 column: 'Variable Names'")
	else:
		if not all(item in plate_variables["Variable Names"].values for item in ['Name Map DNA Parts', 'Number of Parts']):
			raise Exception("'PerPlateVariables' sheet table needs to have 2 rows with the following names: 'Name Map DNA Parts', 'Number of Parts'")
		
	if not all(item in list(pip_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'PipetteVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in pip_variables["Variable Names"].values for item in ['API Name Right Pipette', 'API Name Left Pipette', 'API Name Tiprack Left Pipette', 'API Name Tiprack Right Pipette', 'Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks']):
			raise Exception("'PipetteVariables' sheet table needs to have 7 rows with the following names: 'API Name Right Pipette', 'API Name Left Pipette', 'API Name Tiprack Left Pipette', 'API Name Tiprack Right Pipette', 'Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks'")
		
	if not all(item in list(module_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'ModuleVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in module_variables["Variable Names"].values for item in ['Presence Thermocycler', 'Presence Heater-Shaker', 'Final Open Lid', 'Temperature Lid', 'Hold Block Temperature After Profile', 'RPM Heater-Shaker', 'API Name Heater-Shaker Labware', 'Pause Before Temperature Program', 'Initial Thermocycle Block Temperature']):
			raise Exception("'ModuleVariables' sheet table needs to have 9 rows with the following names: 'Presence Thermocycler', 'Presence Heater-Shaker', 'Final Open Lid', 'Temperature Lid', 'Hold Block Temperature After Profile', 'RPM Heater-Shaker', 'API Name Heater-Shaker Labware', 'Pause Before Temperature Program', 'Initial Thermocycle Block Temperature'")
		
	if not all(item in list(combinations_variables.columns) for item in ["Acceptor Plasmid", "Name"]):
		raise Exception("'Combinations' sheet table needs to have at least 2 columns: 'Name' and 'Acceptor Plasmid'")
	
	if "TemperatureProfile" in name_sheets:
		temperature_variables = excel_variables.get("TemperatureProfile")
		user_variables = UserVariables(excel_variables.get("GeneralVariables"), excel_variables.get("PerPlateVariables"), excel_variables.get("PipetteVariables"),excel_variables.get("ReactionVariables"),excel_variables.get("ModuleVariables"),excel_variables.get("Combinations"),excel_variables.get("TemperatureProfile"))
	else:
		user_variables = UserVariables(excel_variables.get("GeneralVariables"), excel_variables.get("PerPlateVariables"), excel_variables.get("PipetteVariables"),excel_variables.get("ReactionVariables"),excel_variables.get("ModuleVariables"),excel_variables.get("Combinations"))

	user_variables.check(protocol)
	program_variables = SettedParameters(len(protocol.deck))
	program_variables.assign_variables(user_variables, protocol)
	
	# Let's do the check of volumes that can be picked by the set pipettes, this could have been done before because we didnt have the pipettes
	try:
		if user_variables.restrictionEnzymeVolume + user_variables.ligaseVolume + user_variables.bufferVolume + user_variables.serumVolume > 0:
			give_me_optimal_pipette (user_variables.restrictionEnzymeVolume + user_variables.ligaseVolume + user_variables.bufferVolume + user_variables.serumVolume, program_variables.pipR, program_variables.pipL)
	except NotSuitablePipette:
		raise Exception("Reactive mix volume cannot be picked by any of the set pipettes")
	
	try:
		if user_variables.acceptorVolume > 0:
			give_me_optimal_pipette (user_variables.acceptorVolume, program_variables.pipR, program_variables.pipL)
		if user_variables.moduleVolume > 0:
			give_me_optimal_pipette (user_variables.moduleVolume, program_variables.pipR, program_variables.pipL)
	except NotSuitablePipette:
		raise Exception("Either the volume of the acceptor or the volume of the module cannot be picked by set pipettes")
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Setting Labware
	# Setting the HS needed because they have more restrictions in the OT-2 and cannot be done with the setting labware function because setting the HS in a position will not give errors but after it wont work
	# First let's find how many tubes we need of mixes in case we have the HS
	if user_variables.presenceHS and program_variables.volTotalFactor > 0:
		first_key = list(labware_context.get_labware_definition(user_variables.APINameLabwareHS)["wells"].keys())[0]
		vol_max_tube = labware_context.get_labware_definition(user_variables.APINameLabwareHS)["wells"][first_key]["totalLiquidVolume"]
		number_wells_labware = len(labware_context.get_labware_definition(user_variables.APINameLabwareHS)["wells"])
		number_tubes_mix_hs, reactions_per_tube_mix_hs, volumes_tubes_mix_hs = number_tubes_needed (program_variables.volTotalFactor, program_variables.sumSamples, vol_max_tube*0.9)
		
		program_variables.mixWells["Reactions Per Tube"] = reactions_per_tube_mix_hs
		program_variables.mixWells["Volumes"] = volumes_tubes_mix_hs
		program_variables.mixWells["Positions"] = []
		program_variables.mixWells["Definition Liquid"] = protocol.define_liquid(name = "Mix Tube", description = "Mix of recatives MoClo Assembly Reaction. Leave empty!", display_color = "#d3cfcf")
		
		number_hs = math.ceil(number_tubes_mix_hs/number_wells_labware)
		
		# You cannot put the HS in some positions, even if the opentrons app doesnt raise errors
		possible_positions_HS = {key: program_variables.deckPositions[key] for key in [1, 3, 4, 6, 7, 10]}

		# Establish the hs_mod if possible
		hs_mods = setting_labware(number_hs, "heaterShakerModuleV1", possible_positions_HS, protocol, module = True)

		for position, hs_mod in hs_mods.items():
			hs_mod.close_labware_latch()
			hs_mod.load_labware(user_variables.APINameLabwareHS, label = f"Eppendorf Rack with Mix on Slot {position}")
			program_variables.deckPositions[position] = "Heater Shaker"
			program_variables.hs_mods[position] = hs_mod
			
		# Set the volumes of the mixes in case the HS is present
		wells_hs = []
		for hs in list(program_variables.hs_mods.values()):
			wells_hs += hs.labware.wells()
		generator_wells_hs = generator_positions(wells_hs)

		for volume_tube in program_variables.mixWells["Volumes"]:
			well_tube_eppendorf = next(generator_wells_hs)
			program_variables.mixWells["Positions"].append(well_tube_eppendorf)
			well_tube_eppendorf.load_liquid(liquid = program_variables.mixWells["Definition Liquid"],volume = 0)
	
	# Setting the Labware that we already now how many of them we have
	# Source plates
	labels = []
	for labware_source in list(program_variables.samplePlates.values()):
		labels.append(labware_source['Label'])
	labware_source = setting_labware(user_variables.numberSourcePlates, user_variables.APINameSamplePlate, program_variables.deckPositions, protocol, label = labels)
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_source}
	# Now we assign each labware position to ther place in the SetteParameters class
	for index_labware, labware in enumerate(labware_source.items()):
		program_variables.samplePlates[index_labware]["Position"] = labware[0]
		program_variables.samplePlates[index_labware]["Opentrons Place"] = labware[1]
		program_variables.samplePlates[index_labware]['Map Names'] = pd.read_excel("/data/user_storage/VariablesMoCloAssembly.xlsx", sheet_name = user_variables.nameSheetMapParts[index_labware], index_col = 0, engine = "openpyxl")
		# program_variables.samplePlates[index_labware]['Map Names'] = pd.read_excel("VariablesMoCloAssembly.xlsx", sheet_name = user_variables.nameSheetMapParts[index_labware], index_col = 0, engine = "openpyxl")
		program_variables.samplePlates[index_labware]['Map Volumes'] = pd.DataFrame(0, index = list(program_variables.samplePlates[index_labware]["Opentrons Place"].rows_by_name().keys()), columns = list(program_variables.samplePlates[index_labware]["Opentrons Place"].columns_by_name().keys()))
		program_variables.samplePlates[index_labware]['Map Liquid Definitions'] = pd.DataFrame(np.nan, index = list(program_variables.samplePlates[index_labware]["Opentrons Place"].rows_by_name().keys()), columns = list(program_variables.samplePlates[index_labware]["Opentrons Place"].columns_by_name().keys()))
		
		# Let's check that the labware and map have the same names of the rows and columns
		row_names = list(labware[1].rows_by_name().keys())
		columns_names = list(labware[1].columns_by_name().keys())

		rows_map = list(program_variables.samplePlates[index_labware]['Map Names'].index.values)
		columns_map = list(map(str, list(program_variables.samplePlates[index_labware]['Map Names'].columns.values)))

		if row_names != rows_map or columns_names != columns_map:
			raise Exception(f"""
The columns and rows of the Maps of DNA Parts {user_variables.nameSheetMapParts[index_labware]} need to have the same names as the ones in {user_variables.APINameSamplePlate}:
		Labware Names:
		 - Column names: {columns_names}
		 - Row names: {row_names}
		Your names:
		 - Sheet Columns: {columns_map}
		 - Sheet Rows: {rows_map}""")
	
		# Define volumes of each part and their liquid definition
		for combination in program_variables.combinations.values():
			# Let's see if the acceptor of this combination is in the map of this labware
			well = program_variables.samplePlates[index_labware]['Map Names'][program_variables.samplePlates[index_labware]['Map Names'].isin([combination["acceptor"]])].stack()
			if len(well) > 0: # If it enters this loop, the acceptor is in this labware
				row_well, column_well = well.index[0]
				program_variables.samplePlates[index_labware]['Map Volumes'].loc[row_well,str(column_well)] += user_variables.acceptorVolume
				
				# Definition of acceptor liquid
				if pd.isna(program_variables.samplePlates[index_labware]['Map Liquid Definitions'].loc[row_well,str(column_well)]):
					while True:
						color_liquid = f"#{random.randint(0, 0xFFFFFF):06x}"
						if color_liquid.lower() not in program_variables.colors_mediums:
							program_variables.samplePlates[index_labware]['Map Liquid Definitions'].loc[row_well,str(column_well)] = protocol.define_liquid(
								name = combination["acceptor"],
								description = f"",
								display_color = color_liquid
							)
							program_variables.colors_mediums.append(color_liquid)
							break
				
				
			for dna_module in combination["modules"]:
				well = program_variables.samplePlates[index_labware]['Map Names'][program_variables.samplePlates[index_labware]['Map Names'].isin([dna_module])].stack()
				if len(well) > 0:
					row_well, column_well = well.index[0]
					program_variables.samplePlates[index_labware]['Map Volumes'].loc[row_well,str(column_well)] += user_variables.moduleVolume
					
					# Definition of liquid
					if pd.isna(program_variables.samplePlates[index_labware]['Map Liquid Definitions'].loc[row_well,str(column_well)]):
						while True:
							color_liquid = f"#{random.randint(0, 0xFFFFFF):06x}"
							if color_liquid.lower() not in program_variables.colors_mediums:
								program_variables.samplePlates[index_labware]['Map Liquid Definitions'].loc[row_well,str(column_well)] = protocol.define_liquid(
									name = dna_module,
									description = f"",
									display_color = color_liquid
								)
								program_variables.colors_mediums.append(color_liquid)
								break
		
		
		# Check volumes are not higher than vol max of well and load it
		first_key = list(labware_context.get_labware_definition(user_variables.APINameSamplePlate)["wells"].keys())[0]
		vol_max_tube = labware_context.get_labware_definition(user_variables.APINameSamplePlate)["wells"][first_key]["totalLiquidVolume"]
		
		if program_variables.samplePlates[index_labware]['Map Volumes'].ge(vol_max_tube*0.98).any().any():
			raise Exception("There is one or more parts in the map {user_variables.nameSheetMapParts[index_labware]} excedes 0*98 max volume of {user_variables.APINameSamplePlate}, try another combination of variables")
		
		# Now we load the liquids in their wells
		for row in program_variables.samplePlates[index_labware]['Map Names'].index:
			for column in program_variables.samplePlates[index_labware]['Map Names'].columns:
				if not pd.isna(program_variables.samplePlates[index_labware]['Map Names'].loc[row][column]):
					labware[1].wells_by_name()[f"{row}{column}"].load_liquid(liquid = program_variables.samplePlates[index_labware]['Map Liquid Definitions'].loc[row,str(column)], volume = math.ceil(program_variables.samplePlates[index_labware]['Map Volumes'].loc[row,str(column)]))	
	
	# Final Plates
	if user_variables.presenceTermo:
		program_variables.tc_mod.load_labware(user_variables.APINameFinalPlate, label = "Final Plate with Combinations Slot 7")
		labware_final = {7: program_variables.tc_mod.labware}
	else:
		labware_final = setting_labware(len(program_variables.finalPlates), user_variables.APINameFinalPlate, program_variables.deckPositions, protocol, label = "Final Plate With Combinations")
		program_variables.deckPositions = {**program_variables.deckPositions , **labware_final}
	# Now we are going to assign to which final plates the samples from the source plates should go
	for index_labware, labware in enumerate(labware_final.items()):
		program_variables.finalPlates[index_labware]["Position"] = labware[0]
		program_variables.finalPlates[index_labware]["Opentrons Place"] = labware[1]
		program_variables.finalPlates[index_labware]["Map Combinations"] = MapLabware(labware[1])
	
	# Reactive plates and mix (if Heater-Shaker is False)
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Setting the coldblocks that we need for the reactives
	# Let's find how many tubes we need for all the reactives
	first_key = list(labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"].keys())[0]
	vol_max_tube = labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"][first_key]["totalLiquidVolume"]
	
	total_number_tubes = 0
	
	number_tubes_ligase, program_variables.reactiveWells["Ligase"]["Reactions Per Tube"], program_variables.reactiveWells["Ligase"]["Volumes"] = number_tubes_needed (program_variables.volLigaseFactor, program_variables.reactiveWells["Ligase"]["Number Total Reactions"], vol_max_tube*0.9)
	total_number_tubes += number_tubes_ligase
	
	number_tubes_re, program_variables.reactiveWells["RE"]["Reactions Per Tube"], program_variables.reactiveWells["RE"]["Volumes"] = number_tubes_needed (program_variables.volREFactor, program_variables.reactiveWells["RE"]["Number Total Reactions"], vol_max_tube*0.9)
	total_number_tubes += number_tubes_re
	
	number_tubes_buffer, program_variables.reactiveWells["Buffer"]["Reactions Per Tube"], program_variables.reactiveWells["Buffer"]["Volumes"] = number_tubes_needed (program_variables.volBufferFactor, program_variables.reactiveWells["Buffer"]["Number Total Reactions"], vol_max_tube*0.9)
	total_number_tubes += number_tubes_buffer
	
	number_tubes_serum, program_variables.reactiveWells["Serum"]["Reactions Per Tube"], program_variables.reactiveWells["Serum"]["Volumes"] = number_tubes_needed (program_variables.volSerumFactor, program_variables.reactiveWells["Serum"]["Number Total Reactions"], vol_max_tube*0.9)
	total_number_tubes += number_tubes_serum
	
	if user_variables.presenceHS == False and program_variables.volTotalFactor > 0:
		number_tubes_mix, program_variables.mixWells["Reactions Per Tube"], program_variables.mixWells["Volumes"] = number_tubes_needed (program_variables.volTotalFactor, program_variables.sumSamples, vol_max_tube*0.9)
		program_variables.mixWells["Positions"] = []
		total_number_tubes += number_tubes_mix
		program_variables.mixWells["Definition Liquid"] = protocol.define_liquid(name = "Mix Tube", description = "Mix of recatives MoClo Assembly Reaction. Leave Empty!", display_color = "#d3cfcf")
	
	# Last, we need to calculate the ammount of water we need to transfer to each well and the sum to kjnow the tubes
	# We need to calculate it in anouther way, not with number_tubes_needed because it is not an uniform ammount of water
	volume_every_well = []
	for combination_name, combination in program_variables.combinations.items():
		volume_with_modules = program_variables.volTotal + user_variables.acceptorVolume + user_variables.moduleVolume*(len(combination["modules"]))
		# Let's check if the combinations made make any sense, in other words, if the volTotal+acceptor+modules < volFinal
		if volume_with_modules > user_variables.finalVolume:
			raise Exception (f"For the combination {combination_name} the sum of reagents, acceptor plasmid and modules volumes, {volume_with_modules}ul, is greater than the final volume, {user_variables.finalVolume}ul")
		else:																								
			volume_every_well.append(volume_with_modules)
	
	# lets calculate the volume of water in each well
	volume_water_every_well = [user_variables.finalVolume-i for i in volume_every_well]
	# lets calculate the water needed
	all_water_needed = sum(volume_water_every_well)
	
	if any(volume+(vol_max_tube*0.1) > vol_max_tube for volume in volume_water_every_well) == True:
		raise Exception("One of the volumes of water does not fit in tubes (adding pipetting extra volume which is the 0.1 of the maximum volume of the Eppendorfs Labware), check combinations, maxime volume of tubes or final reaction volume")
	
	if all_water_needed <= vol_max_tube:
		all_tubes = [volume_water_every_well]
		program_variables.reactiveWells["Water"]["Volumes"] = [all_water_needed]
	
	else:
		current_tube = []
		all_tubes = []
		for i, element in enumerate(volume_water_every_well):
			if sum(current_tube)+element+20 <= vol_max_tube:
				current_tube.append(element)
			else:
				all_tubes.append(current_tube)
				current_tube = [element]
			
			if i == len(volume_water_every_well)-1:
				all_tubes.append(current_tube)
		program_variables.reactiveWells["Water"]["Volumes"] = [sum(volumes_tube) for volumes_tube in all_tubes]
		
	# Now we will come with volume and number of tubes
	if all_water_needed > 0:
		total_number_tubes += len(all_tubes)
	
	
	program_variables.reactiveWells["Water"]["Volumes Per Tube"] = all_tubes # similar to Reactions Per Tube but with volumes instead of the reactions
	program_variables.reactiveWells["Water"]["Positions"] = []
	
	
	# Set the number of tubes in the coldblock
	number_coldblocks = math.ceil(total_number_tubes/len(labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"]))
	coldblocks = setting_labware(number_coldblocks, user_variables.APINameEppendorfPlate, dict(sorted(program_variables.deckPositions.items(), reverse=True)), protocol, label = "Reagents") # We do the inverse deckPositions because it is less likely to have deck conflict error
	program_variables.deckPositions = {**program_variables.deckPositions , **coldblocks}
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Set the places of the reagents and fill the dictionaries of the different kind of labwares
	# Start with the coldblock(s) labware that for sure it is in it
	positions_eppendorfs = []
	for labware in coldblocks.values():
		positions_eppendorfs += labware.wells()
	generator_positions_reagents = generator_positions(positions_eppendorfs)
	
	# Assign to each reactive the positions on the coldblock(s)
	for reagent_type in program_variables.reactiveWells.keys():
		for volume_tube in program_variables.reactiveWells[reagent_type]["Volumes"]:
			if volume_tube > 0:
				well_tube_eppendorf = next(generator_positions_reagents)
				program_variables.reactiveWells[reagent_type]["Positions"].append(well_tube_eppendorf)
				well_tube_eppendorf.load_liquid(liquid = program_variables.reactiveWells[reagent_type]["Definition Liquid"], volume = math.ceil(volume_tube))
	
	# Now we state the mix tubes, which can go in the HS or the Coldblock
	if user_variables.presenceHS == False:
		for volume_tube in program_variables.mixWells["Volumes"]:
			well_tube_eppendorf = next(generator_positions_reagents)
			program_variables.mixWells["Positions"].append(well_tube_eppendorf)
			well_tube_eppendorf.load_liquid(liquid = program_variables.mixWells["Definition Liquid"], volume = 0)
			
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Set the block temperature before doing anything
	if user_variables.presenceTermo and not pd.isna(user_variables.initialTemperatureBlock):
		program_variables.tc_mod.set_block_temperature(user_variables.initialTemperatureBlock)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# We are goign to distribute water and reagents mix
	
	# First, lets find in which wells of the final plate we need to create the combinations
	index_start_final_plate = opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)
	wells_distribute = []
	for final_labware in program_variables.finalPlates.values():
		wells_distribute += final_labware["Opentrons Place"].wells()
	wells_distribute_free = wells_distribute[index_start_final_plate:int(index_start_final_plate+program_variables.sumSamples)]
	
	# Transfer the Water, that is a variable ammount depending on the well
	# We are going to do it with every tube the same
	well_start = 0
	
	last_pipette_used = program_variables.pipR # Just initialize
	
	for index_tube, tube_water in enumerate(program_variables.reactiveWells["Water"]["Positions"]):
		# First, let's find the volumes that we have to distribute with the 2 pipettes
		volWaterPipR, posWaterPipR, volWaterPipL, posWaterPipL = vol_pipette_matcher (program_variables.reactiveWells["Water"]["Volumes Per Tube"][index_tube], wells_distribute_free[well_start:well_start+len(program_variables.reactiveWells["Water"]["Volumes Per Tube"][index_tube])], program_variables.pipR, program_variables.pipL)
		
		well_start += len(program_variables.reactiveWells["Water"]["Volumes Per Tube"][index_tube])
		
		position_tube = program_variables.reactiveWells["Water"]["Positions"][index_tube]
		
		# Define last_pipette_used tipracks
		if last_pipette_used.mount == "right":
			tiprack = user_variables.APINameTipR
			starting_tip = user_variables.startingTipPipR
		else:
			tiprack = user_variables.APINameTipL
			starting_tip = user_variables.startingTipPipL

		# Transfer with the last pipette if there is some position to distrtiibute with it
		# This part has a lot of optimizing, I think the program could be easier in this part
		if last_pipette_used == program_variables.pipR and posWaterPipR:
			if not last_pipette_used.has_tip:
				check_tip_and_pick(last_pipette_used, tiprack, program_variables.deckPositions, protocol, initial_tip = starting_tip, replace_tiprack = user_variables.replaceTiprack, same_tiprack = program_variables.sameTipRack)
			last_pipette_used.distribute(volWaterPipR, position_tube, posWaterPipR, new_tip = "never", touch_tip = True, disposal_volume = 0)
		elif last_pipette_used == program_variables.pipL and posWaterPipL:
			if not last_pipette_used.has_tip:
				check_tip_and_pick(last_pipette_used, tiprack, program_variables.deckPositions, protocol, initial_tip = starting_tip, replace_tiprack = user_variables.replaceTiprack, same_tiprack = program_variables.sameTipRack)
			last_pipette_used.distribute(volWaterPipL, position_tube, posWaterPipL, new_tip = "never", touch_tip = True, disposal_volume = 0)
			
		# Transfer with the other pipette
		if last_pipette_used == program_variables.pipR and posWaterPipL:
			if last_pipette_used != None and last_pipette_used.has_tip:
				last_pipette_used.drop_tip()
			check_tip_and_pick(program_variables.pipL, user_variables.APINameTipL,program_variables.deckPositions, protocol, initial_tip = user_variables.startingTipPipL, replace_tiprack = user_variables.replaceTiprack, same_tiprack = program_variables.sameTipRack)
			last_pipette_used = program_variables.pipL
			last_pipette_used.distribute(volWaterPipL, position_tube, posWaterPipL, new_tip = "never", touch_tip = True, disposal_volume = 0)
		elif last_pipette_used == program_variables.pipL and posWaterPipR:
			if last_pipette_used != None and last_pipette_used.has_tip:
				last_pipette_used.drop_tip()
			last_pipette_used = program_variables.pipR
			check_tip_and_pick(program_variables.pipR, user_variables.APINameTipR, program_variables.deckPositions, protocol, initial_tip = user_variables.startingTipPipR, replace_tiprack = user_variables.replaceTiprack, same_tiprack = program_variables.sameTipRack)
			last_pipette_used.distribute(volWaterPipR, position_tube, posWaterPipR, new_tip = "never", touch_tip = True, disposal_volume = 0)
	
	# We drop the tip of the last used pipette because we are goiing to transfer the rest of the reactives
	if last_pipette_used.has_tip:
		last_pipette_used.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Create the mixes
	# Lower the aspiration and dispense rate for the ligase and RE becaus ethey are in a very viscous medium
	if program_variables.pipR != None:
		default_values_pipR = [program_variables.pipR.flow_rate.aspirate, program_variables.pipR.flow_rate.dispense]
		program_variables.pipR.flow_rate.aspirate = program_variables.pipR.min_volume
		program_variables.pipR.flow_rate.dispense= program_variables.pipR.min_volume
	if program_variables.pipL != None:
		default_values_pipL = [program_variables.pipL.flow_rate.aspirate, program_variables.pipL.flow_rate.dispense]
		program_variables.pipL.flow_rate.aspirate = program_variables.pipL.min_volume
		program_variables.pipL.flow_rate.dispense= program_variables.pipL.min_volume
	
	# Transfer Ligase
	if program_variables.volLigaseFactor > 0:
		tube_to_tube_transfer(program_variables.volLigaseFactor, program_variables.reactiveWells["Ligase"]["Positions"], program_variables.reactiveWells["Ligase"]["Reactions Per Tube"], program_variables.mixWells["Positions"], program_variables.mixWells["Reactions Per Tube"][:], program_variables, user_variables, protocol)
	
	# Transfer RE
	if program_variables.volREFactor > 0:
		tube_to_tube_transfer(program_variables.volREFactor, program_variables.reactiveWells["RE"]["Positions"], program_variables.reactiveWells["RE"]["Reactions Per Tube"], program_variables.mixWells["Positions"], program_variables.mixWells["Reactions Per Tube"][:], program_variables, user_variables, protocol)
	
	if program_variables.pipR != None:
		program_variables.pipR.flow_rate.aspirate = default_values_pipR[0]
		program_variables.pipR.flow_rate.dispense= default_values_pipR[1]
	if program_variables.pipL != None:
		program_variables.pipL.flow_rate.aspirate = default_values_pipL[0]
		program_variables.pipL.flow_rate.dispense=default_values_pipL[1]
	
	# Transfer Buffer
	if program_variables.volBufferFactor > 0:
		tube_to_tube_transfer(program_variables.volBufferFactor, program_variables.reactiveWells["Buffer"]["Positions"], program_variables.reactiveWells["Buffer"]["Reactions Per Tube"], program_variables.mixWells["Positions"], program_variables.mixWells["Reactions Per Tube"][:], program_variables, user_variables, protocol)
	
	# Transfer Serum
	if program_variables.volSerumFactor > 0:
		tube_to_tube_transfer(program_variables.volSerumFactor, program_variables.reactiveWells["Serum"]["Positions"], program_variables.reactiveWells["Serum"]["Reactions Per Tube"], program_variables.mixWells["Positions"], program_variables.mixWells["Reactions Per Tube"][:], program_variables, user_variables, protocol)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Mix and Distribute Sets
	# We are going to use "wells_distribute_free" because it is the same wells that we need to distribute the mix
	if program_variables.volTotal > 0:
		optimal_pipette = give_me_optimal_pipette (program_variables.volTotal, program_variables.pipR, program_variables.pipL)

		if optimal_pipette.mount == "right":
			tiprack = user_variables.APINameTipR
			starting_tip = user_variables.startingTipPipR
		else:
			tiprack = user_variables.APINameTipL
			starting_tip = user_variables.startingTipPipL

		wells_distribute_mix = wells_distribute_free[:]
		for index, tube in enumerate(program_variables.mixWells["Positions"]):
			if user_variables.presenceHS == True:
				# Find out in which HS is the tube and shake it
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].set_and_wait_for_shake_speed(user_variables.rpm)
				protocol.delay(seconds=15)
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].deactivate_shaker()
				if optimal_pipette.has_tip == False:
					check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, initial_tip = starting_tip, same_tiprack = program_variables.sameTipRack, replace_tiprack = user_variables.replaceTiprack)
				optimal_pipette.distribute(float(program_variables.volTotal), tube, wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]], new_tip="never", disposal_volume=0)
			
			else:
				# Mix it with a pipette
				# First we find out what is the mixing volume and the pipette to mix
				vol_mixing = program_variables.mixWells["Volumes"][index] / 3
				optimal_pipette_mixing = give_me_optimal_pipette(vol_mixing, program_variables.pipR, program_variables.pipL)
				if optimal_pipette_mixing.max_volume < vol_mixing:
					vol_mixing = optimal_pipette_mixing.max_volume
				
				if optimal_pipette_mixing.mount == "right":
					tiprack_mix = user_variables.APINameTipR
					starting_tip_mix = user_variables.startingTipPipR
				else:
					tiprack_mix = user_variables.APINameTipL
					starting_tip_mix = user_variables.startingTipPipL
				if optimal_pipette_mixing.has_tip == False:
					check_tip_and_pick(optimal_pipette_mixing, tiprack_mix, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = starting_tip_mix, same_tiprack = program_variables.sameTipRack)
				
				# Now we mix
				mixing_eppendorf_15(tube, program_variables.mixWells["Volumes"][index], vol_mixing, optimal_pipette_mixing, protocol)
				
				# Distribute the reactions of that tube
				if optimal_pipette == optimal_pipette_mixing:
					optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]], new_tip="never", disposal_volume=0)
				else:
					optimal_pipette_mixing.drop_tip()
					check_tip_and_pick (optimal_pipette, tiprack, program_variables.deckPositions, protocol, initial_tip = starting_tip, same_tiprack = program_variables.sameTipRack, replace_tiprack = user_variables.replaceTiprack)
					optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]], new_tip="never", disposal_volume=0)
					
			del wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]]
		optimal_pipette.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Distribute DNA parts and acceptor module to the different final wells
	
	generator_final_wells = generator_positions (wells_distribute_free)

	# Check the optimal pipette for acceptor and modules
	if user_variables.acceptorVolume > 0:
		optimal_pipette_acceptor = give_me_optimal_pipette (user_variables.acceptorVolume, program_variables.pipR, program_variables.pipL)
		
		if optimal_pipette_acceptor == "right":
			tiprack_acceptor = user_variables.APINameTipR
			starting_tip_acceptor = user_variables.startingTipPipR
		else:
			tiprack_acceptor = user_variables.APINameTipL
			starting_tip_acceptor = user_variables.startingTipPipL
	
	if user_variables.moduleVolume > 0:
		optimal_pipette_module = give_me_optimal_pipette (user_variables.moduleVolume, program_variables.pipR, program_variables.pipL)
		
		if optimal_pipette_module == "right":
			tiprack_module = user_variables.APINameTipR
			starting_tip_module = user_variables.startingTipPipR
		else:
			tiprack_module = user_variables.APINameTipL
			starting_tip_module = user_variables.startingTipPipL
	

	

	for name_combination, parts_combination in program_variables.combinations.items():
		# Set the final well
		well_final_combination = next(generator_final_wells)
		
		if user_variables.acceptorVolume > 0:
			# Take well where the acceptor is
			all_well_acceptor = find_well_by_value (parts_combination["acceptor"], program_variables.samplePlates)
			if len(all_well_acceptor) != 1:
				raise Exception(f"The acceptor '{parts_combination['acceptor']}' is located in more than 1 well in the given maps, this protocol only allows one tube per part")
			else:
				well_acceptor = all_well_acceptor[0]
			# Transfer the acceptor
			check_tip_and_pick (optimal_pipette_acceptor, tiprack_acceptor, program_variables.deckPositions, protocol, initial_tip = starting_tip_acceptor, same_tiprack = program_variables.sameTipRack, replace_tiprack = user_variables.replaceTiprack)
			optimal_pipette_acceptor.transfer(user_variables.acceptorVolume, well_acceptor, well_final_combination, new_tip = "never")
			optimal_pipette_acceptor.drop_tip()
		
		
		# Transfer all the DNA parts that will contain the final constructs
		if user_variables.moduleVolume > 0:
			for part_plasmid in parts_combination["modules"]:
				# Take the module part
				all_well_source_DNApart = find_well_by_value (part_plasmid, program_variables.samplePlates)
				if len(all_well_source_DNApart) != 1:
					raise Exception(f"The module part '{part_plasmid}' is located in more than 1 well in the given maps, this protocol only allows one tube per part")
				else:
					well_source_DNApart = all_well_source_DNApart[0]

				# Transfer the module volume
				check_tip_and_pick (optimal_pipette_module, tiprack_module, program_variables.deckPositions, protocol, initial_tip = starting_tip_module, same_tiprack = program_variables.sameTipRack, replace_tiprack = user_variables.replaceTiprack)
				optimal_pipette_module.transfer(user_variables.moduleVolume, well_source_DNApart, well_final_combination, new_tip = "never")
				optimal_pipette_module.drop_tip()
		
		# Map where is this combination
		for finalplate in program_variables.finalPlates.values():
			if str(finalplate["Position"]) == str(well_final_combination).split(" ")[-1]:
				finalplate["Map Combinations"].assign_value(name_combination, well_final_combination._core._row_name, well_final_combination._core._column_name)
				
	# Export map(s) in an excel
	writer = pd.ExcelWriter(f'/data/user_storage/{user_variables.finalMapName}.xlsx', engine='openpyxl')
	# writer = pd.ExcelWriter(f'{user_variables.finalMapName}.xlsx', engine='openpyxl')
	
	for final_plate in program_variables.finalPlates.values():
		final_plate["Map Combinations"].map.to_excel(writer, sheet_name = f"CombinationsSlot{final_plate['Position']}")
	
	writer.save()
	
	# Perform PCR profile
	if user_variables.presenceTermo:
		if user_variables.pause:
			protocol.pause("Protocol is pause so plate in thermocyler can be mixed and/or user can put caps on it")
		
		program_variables.tc_mod.close_lid()
		run_program_thermocycler(program_variables.tc_mod, user_variables.temperatureProfile, user_variables.temperatureLid, user_variables.finalVolume, protocol, final_lid_state = user_variables.finalStateLid, final_block_state = user_variables.finalTemperatureBlock)
	
	# Final home
	protocol.home()
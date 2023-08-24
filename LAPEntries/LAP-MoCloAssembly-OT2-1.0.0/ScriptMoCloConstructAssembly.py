"""
Python script destined to OT-2
This script performs a merge of samples from N source plates to a lower amount of final plates
This script needs an excel file attached to perform the running
For more info go to https://github.com/Biocomputation-CBGP/LAPrepository/tree/main/LAPEntries and/or
https://github.com/Biocomputation-CBGP/OT2/tree/main/GoldenStandardAssembly and/or
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
		
		# Check all the boolean values and setting them
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
		
		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if len(self.samplesPerPlate) < (self.numberSourcePlates + 1) or len(self.nameSheetMapParts) < (self.numberSourcePlates + 1):
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
			
			# If exists we will check it has same number of rows and columns at least, when labware is load we will check the names
			map_rows, map_columns = map_content.shape
			if map_rows != len(definition_source_plate["ordering"][0]) or map_columns != len(definition_source_plate["ordering"]):
				raise Exception(f"The Sheet '{name_map}' needs to have the same columns and rows as the labware '{self.APINameSamplePlate}'. If there is no part in a position, leave cell empty")
			
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
		
		# Check if any combination list name is repeated
		if pd.Series(self.combinations_dataframe["Name"].values).is_unique == False:
			raise Exception("Names on the Combinations Sheet have to be unique")
		
		# Check that there is no value on the map is not being used
		all_values_combinations = np.concatenate(self.combinations_dataframe.iloc[:,1:].values).tolist()
		for element in unflat_values:
			if element not in all_values_combinations:
				raise Exception(f"The DNA part '{element}' is not used in any combination. Take it out of the map and run again")

		# Check if the thermocycler is included if we need more than 1 final plate
		if self.presenceTermo and len(self.combinations_dataframe["Name"].values) > len(definition_final_plate["wells"].keys()):
			raise Exception("If the Thermocycler is present, only 1 final plate can be created and all of your combinations does not fit in the selected final labware")			
		
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
	def __init__(self):
		self.pipR = None
		self.pipL = None
		self.samplePlates = {}
		self.finalPlates = {}
		self.reactiveWells = {}
		self.mixWells = {"Reactions Per Tube":[], "Volumes":[], "Definition Liquid": None}
		self.deckPositions = {key: None for key in range(1,12)}
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
											  "Label":f"DNA Plate with Map {user_variables.nameSheetMapParts[index_plate]}",
											  "Opentrons Place":None,
											  "Map Names":None,
											  "Map Volumes":None,
											  "Map Liquid Definitions":None}

		self.combinations = generate_combinations_dict(user_variables.combinations_dataframe)
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
	pass

# Functions definitions
# ----------------------------------
# ----------------------------------

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

def number_tubes_needed (vol_reactive_per_reaction_factor, number_reactions, vol_max_tube):
	"""
	Given a maximum volume of the tube (vol_max_tube), the volume of that reactive/reaction (vol_reactive_per_reaction_factor) and the total number of reactions (number_reactions)
	this function will return the number of tubes needed for this reactive and how many reactions are filled in every tube
	
	This function does not garantee the lower number of tubes but it assures that everything can be picked with the pipettes that we have
	
	This function will be used mainly, sometimes exclusively, in setting_number_plates
	"""
	
	number_tubes = 1 # Initizialice the number of tubes
	reactions_per_tube = [number_reactions] # Initialice the reactions per tube
	volumes_tubes = [vol_reactive_per_reaction_factor*number_reactions]*number_tubes # Initialice the number of tubes
	
	while any(volume > vol_max_tube for volume in volumes_tubes): # If there is some volume that is greater than the max volume we are going to enter in the loop
		number_tubes += 1 # We add one tube so the volume can fit in the tubes
		
		# Now we redistribute the reactions (and correspondant volume) to the tubes so it will be the most homogeneus way
		reactions_per_tube = [int(number_reactions/number_tubes)]*number_tubes
		tubes_to_add_reaction = number_reactions%number_tubes
		for i in range(tubes_to_add_reaction):
			reactions_per_tube[i] += 1
		
		# Calculate the new volumes
		volumes_tubes = [vol_reactive_per_reaction_factor*number_reactions_tube for number_reactions_tube in reactions_per_tube]
	
	# When the volume can fit every tube (exit from th ewhile loop) we return the number of tubes and the reactions that will fit in every tube
	return (number_tubes, reactions_per_tube, volumes_tubes)

def generator_positions (labware_wells_name):
	"""
	Generator of the positions to transfer, it will give you the next element of a list every time it is called
	"""
	for well in labware_wells_name:
		yield well

def check_tip_and_pick (pipette_used, position_deck, variables_define_tiprack, protocol):
	"""
	This functions is used to pick tips and in case of need, replace the tiprack or add one to the labware
	This way we add labwares in the process of the simulation and we do not need to calculate it a priori
	
	In the OT-App it will appear directly in the deck but it has been added with this function
	"""
	# One future improvemnt of this function is to check if the pipettes use the same tipracks and add them to both pipettes, that way we will need less tipracks if they
	# have the same tips associated, for exmaple, if we are using a 300 multi and single pipette
	try:
		pipette_used.pick_up_tip()
		# When there are no tips left in the tiprack OT will raise an error
	except OutOfTipsError:
		if len(pipette_used.tip_racks) == 0:
			position_deck = {**position_deck , **define_tiprack(pipette_used, position_deck, variables_define_tiprack, protocol)}
			# We establish now the starting tip, it will only be with the first addition, the rest will be establish that the first tip is in A1 directly
			if pipette_used.mount == "right":
				pipette_used.starting_tip = pipette_used.tip_racks[0][variables_define_tiprack.startingTipPipR]
			elif pipette_used.mount == "left":
				pipette_used.starting_tip = pipette_used.tip_racks[0][variables_define_tiprack.startingTipPipL]
		else:
			if variables_define_tiprack.replaceTiprack == False:
				position_deck = {**position_deck , **define_tiprack(pipette_used, position_deck, variables_define_tiprack, protocol)}
			else:
				#Careful with this part if you are traspassing this script into jupyter because this will crash your jupyter (will wait until resume and it does not exist)
				protocol.pause("Replace Empty Tiprack With A Full One And Press Resume In OT-APP")
				pipette_used.reset_tipracks()
		
		#Finally, we pick up the needed tip        
		pipette_used.pick_up_tip()
	
	return
	
def define_tiprack (pipette, position_deck, variables_define_tiprack, protocol):
	positions_free = [position for position, labware in position_deck.items() if labware == None]
	
	if pipette.mount == "right":
		tiprack_name = variables_define_tiprack.APINameTipR
	else:
		tiprack_name = variables_define_tiprack.APINameTipL
	
	if len(positions_free) == 0:
		raise Exception("There is not enough space in the deck for this protocol, try less samples")
	
	for position in positions_free:
		try:
			tiprack = protocol.load_labware(tiprack_name, position)
			position_deck[position] = tiprack_name
		except DeckConflictError:
			continue
		
		if variables_define_tiprack.APINameTipR == variables_define_tiprack.APINameTipL:
			protocol.loaded_instruments["right"].tip_racks.append(tiprack)
			protocol.loaded_instruments["left"].tip_racks.append(tiprack)
		else:
			if pipette.mount == "right":
				protocol.loaded_instruments["right"].tip_racks.append(tiprack)
			elif pipette.mount == "left":
				protocol.loaded_instruments["left"].tip_racks.append(tiprack)
		
		# If it has reached this point it means that the tiprack has been defined
		return {position:tiprack_name}

def optimal_pipette_use (aVolume, pipette_r, pipette_l):
	"""
	Function that will return the optimal pipette to use for the volume that we want to handle.
	
	In case that it is a great volume (higher than the maximal volume of both pipettes) will return the pipette that will give the minimal quantity of movements
	
	If none of the pipettes attached can pick the volume (because it is too small) the function will raise an error
	
	For the correct functioning of this function at least 1 pipette should be attached to the OT, otherwise, the function will raise an error
	"""

	if pipette_r == None and pipette_l == None: #no pipettes attached
		raise Exception("There is not a pippette attached")
	
	# First we look if one of them is the only option
	elif pipette_r == None or pipette_l == None: # One mount is free, only need that the volume is more than the min of the pipette
		if pipette_r == None and aVolume >= pipette_l.min_volume:
			return pipette_l
		elif pipette_l == None and aVolume >= pipette_r.min_volume:
			return pipette_r
		else: # One of them does not exist and the other one is not valid
			raise NotSuitablePipette
			
	else: # Both of them are in the OT
		# Define which has a bigger min volume so it can do the fewer moves to take the reactives or even distribute with fewer moves
		if pipette_l.min_volume > pipette_r.min_volume:
			max_pipette = pipette_l
			min_pipette = pipette_r
		else:
			max_pipette = pipette_r
			min_pipette = pipette_l
		
		if aVolume >= pipette_l.min_volume and aVolume >= pipette_r.min_volume:
			if pipette_l == max_pipette:
				return pipette_l
			else:
				return pipette_r
		elif aVolume >= pipette_l.min_volume and pipette_l == min_pipette:
			return pipette_l
		elif aVolume >= pipette_r.min_volume and pipette_r == min_pipette:
			return pipette_r
		else: # None of the pipettes can hold that volume
			raise NotSuitablePipette
	return

def run_program_thermocycler(tc_mod, program, lid_temperature, final_lid_state, final_block_state, volume_sample, protocol):
	"""
	Function that will read the csv file with the steps of the program and will perform it
	in the thermocycler
	the program is already the pd.DataFrame, because it has already been read and establish that the lid temperature is okay,
	it exists, etc, i.e., control error of the file
	"""
	
	# initialyze the state of the variable cycle that we will use to control if the step is a cycle or a step
	cycle = False
	
	# set the initail temperature of the lid
	tc_mod.set_lid_temperature(lid_temperature)
	for row in program.iterrows():
		# Check if it is a cycle or not, if it is a start of the end of it
		# This will work because we have already donde contorl of the values of this column which only can be -, Start or End
		if row[1]["Cycle Status"].lower() == "start":
			profile_termo =[{"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])}]
			cycle = True
			continue
		elif row[1]["Cycle Status"].lower() == "end":
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
			tc_mod.execute_profile(steps = profile_termo,
								   repetitions = int(row[1]["Number of Cycles"]),
								   block_max_volume = volume_sample)
			cycle = False
			continue
		
		# Now we know if we have to add a step to the cycle or do the step directly
		if cycle == True:
			profile_termo.append({"temperature":float(row[1]["Temperature"]),"hold_time_seconds":float(row[1]["Time (s)"])})
		elif cycle == False:
			tc_mod.set_block_temperature(row[1]["Temperature"],
										 hold_time_seconds = float(row[1]["Time (s)"]),
										 block_max_volume = volume_sample)
	# Now we are going to put the block at one temeprature/open lid if it is establish like that
	tc_mod.deactivate_lid()
	
	if final_lid_state:
		tc_mod.open_lid()
	
	if pd.isna(final_block_state) == False:
		tc_mod.set_block_temperature(final_block_state,
									 block_max_volume = volume_sample)
	else:
		tc_mod.deactivate_block()
	return

def z_positions_mix (vol_mixing):
	"""
	Function that will define the positions of mixing according to the volume of each tube of primer set
	
	These heights have been manually measured for 1.5mL eppendorfs to attach z to aproximatelly the volume associated
	
	We will have 3 mixing heights at the end, but not neccessarilly different within each other
	"""
	
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
	else:
		pass
	
	return 

def mixing_eppendorf_15 (location_tube, volume_tube, program_variables, user_variables, protocol):
	"""
	This is a function to perfrom an extensive mixing of every eppendorf which should be done before distributing the reactives along the final plates
	
	Mixing is one of the most crucial parts of this workflow and that is why theer is a function only for it
	
	This function will perform the mixing and will return warnings (in case that is needed) and the final pipette that has been used
	"""
	# This function is going to perform the mixing of the tubes in the coldblock (it is setted for the 1500ul eppendorf because the positions are done manually)
	mastermix_mixing_volume_theory = volume_tube / 3
	try:
		aSuitablePippet_mixing = optimal_pipette_use(mastermix_mixing_volume_theory, program_variables.pipR, program_variables.pipL)
		max_vol_pipette = aSuitablePippet_mixing.max_volume
		if max_vol_pipette < mastermix_mixing_volume_theory:
			volume_mixing = max_vol_pipette
		else:
			volume_mixing = mastermix_mixing_volume_theory
			pass
	except NotSuitablePipette: # If this happens it means that the the volume is too low to any of the pipettes
		if program_variables.pipR.min_volume < program_variables.pipL.min_volume:
			volume_mixing = program_variables.pipR.min_volume
			aSuitablePippet_mixing = program_variables.pipR
		else:
			volume_mixing = program_variables.pipL.min_volume
			aSuitablePippet_mixing = program_variables.pipL

	if aSuitablePippet_mixing.has_tip:
		pass
	else:
		if aSuitablePippet_mixing.mount == "right" and program_variables.pipL != None and program_variables.pipL.has_tip:
			program_variables.pipL.drop_tip()
		elif aSuitablePippet_mixing.mount == "left" and program_variables.pipR != None and program_variables.pipR.has_tip:
			program_variables.pipR.drop_tip()
		check_tip_and_pick (aSuitablePippet_mixing, program_variables.deckPositions, user_variables, protocol)
	
	# After calculating the mixing volume, choosing a pipette and picking up a tip we perform the mix
	positions_mixing = z_positions_mix(volume_mixing) # This is the part that is customized for the 1500uL eppendorfs
	
	# We are going to mix 7 times at different heighs of the tube
	aSuitablePippet_mixing.mix(7, volume_mixing, location_tube.bottom(z=positions_mixing[1])) 
	aSuitablePippet_mixing.mix(7, volume_mixing, location_tube.bottom(z=positions_mixing[0])) 
	aSuitablePippet_mixing.mix(7, volume_mixing, location_tube.bottom(z=positions_mixing[2]))
	
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)
	aSuitablePippet_mixing.touch_tip(location_tube,v_offset = -27, radius=0.3, speed=30)
	# Now we are going to aspirate and dispense 3 times at different heights to mix a little bit more the content of the tube
	for i in range(2):
		aSuitablePippet_mixing.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
		aSuitablePippet_mixing.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
	for i in range(2):
		aSuitablePippet_mixing.aspirate(volume_mixing, location_tube.bottom(z=positions_mixing[2]))
		aSuitablePippet_mixing.dispense(volume_mixing, location_tube.bottom(z=positions_mixing[0]))
	aSuitablePippet_mixing.blow_out(location_tube.center())
	
	return aSuitablePippet_mixing

def tube_to_tube_transfer (vol_transfer_reaction, positions_source_tubes, reactions_source_tubes, positions_final_tubes, reactions_final_tubes, program_variables, user_variables, protocol):
	index_source_tube = 0 # Initial
	if program_variables.pipL:
		pipette_use = program_variables.pipL #Initial
	else:
		pipette_use = program_variables.pipR
	for index_final_tube, final_tube in enumerate(positions_final_tubes):
		while reactions_final_tubes[index_final_tube] > 0:
			# calculate how much volume we need to pass from 1 tube to another
			if reactions_source_tubes[index_source_tube] >= reactions_final_tubes[index_final_tube]:
				volume_transfer = vol_transfer_reaction*reactions_final_tubes[index_final_tube]
				reactions_source_tubes[index_source_tube] -= reactions_final_tubes[index_final_tube]
				reactions_final_tubes[index_final_tube] = 0
			else:
				volume_transfer = vol_transfer_reaction*reactions_source_tubes[index_source_tube]
				reactions_source_tubes[index_source_tube] = 0
				reactions_final_tubes[index_final_tube] -= reactions_source_tubes[index_source_tube]
				
			# We choose the pipette that will transfer it
			optimal_pipette = optimal_pipette_use(volume_transfer, program_variables.pipR, program_variables.pipL)
			if optimal_pipette != pipette_use and pipette_use.has_tip:
				pipette_use.drop_tip()
				pipette_use = optimal_pipette
				check_tip_and_pick (pipette_use, program_variables.deckPositions, user_variables, protocol)
			elif optimal_pipette != pipette_use and pipette_use.has_tip == False:
				pipette_use = optimal_pipette
				check_tip_and_pick (pipette_use, program_variables.deckPositions, user_variables, protocol)
			elif optimal_pipette == pipette_use and pipette_use.has_tip:
				pass
			elif optimal_pipette == pipette_use and pipette_use.has_tip == False:
				check_tip_and_pick (pipette_use, program_variables.deckPositions, user_variables, protocol)
			
			# Transfer volume
			pipette_use.transfer(float(volume_transfer), positions_source_tubes[index_source_tube], final_tube, new_tip = "never")

			# Define the source tube
			if reactions_source_tubes[index_source_tube] == 0:
				index_source_tube += 1
	if pipette_use.has_tip:
		pipette_use.drop_tip()
	
	return

def generate_combinations_dict(pd_combination):
	combination_dict = {}
	list_names = list(pd_combination["Name"].values)
	for name_combination in list_names:
		elements_row = [element for element in pd_combination.loc[pd_combination["Name"] == name_combination].values[0][1:] if not pd.isna(element)]
		combination_dict[name_combination] = {"acceptor":elements_row[0], "modules":elements_row[1:]}
	return combination_dict

def find_well_by_value (value, possible_labwares):
	"""
	This labware should have the map of the labwares where the value should be looked for and the position where that labware is
	
	This function will only return the first well with that value
	
	If it doesnt find the value in the labware it will return None
	"""
	for possible_labware in possible_labwares.values():
		cell_pd_value = possible_labware["Map Names"][possible_labware["Map Names"].isin([value])].stack().index # stack() returns a pandas.Series in which the indexes are the (row, column) of the cells that the value is
		if len(cell_pd_value) == 0:
			continue
		if len(cell_pd_value) > 1:
			raise Exception(f"The DNA Part {value} is in the labware {possible_labware['Label']} more than once")
		else:
			well_value = str(cell_pd_value[0][0])+str(cell_pd_value[0][1])
			return possible_labware["Opentrons Place"][well_value]
	raise Exception(f"{value} is not in the provied Maps")

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
	program_variables = SettedParameters()
	program_variables.assign_variables(user_variables, protocol)
	
	# Let's do the check of volumes that can be picked by the set pipettes, this could have been done before because we didnt have the pipettes
	try:
		if user_variables.restrictionEnzymeVolume + user_variables.ligaseVolume + user_variables.bufferVolume + user_variables.serumVolume > 0:
			optimal_pipette_use(user_variables.restrictionEnzymeVolume + user_variables.ligaseVolume + user_variables.bufferVolume + user_variables.serumVolume, program_variables.pipR, program_variables.pipL)
	except NotSuitablePipette:
		raise Exception("Reactive mix volume cannot be picked by any of the set pipettes")
	
	try:
		if user_variables.acceptorVolume > 0:
			optimal_pipette_use(user_variables.acceptorVolume, program_variables.pipR, program_variables.pipL)
		if user_variables.moduleVolume > 0:
			optimal_pipette_use(user_variables.moduleVolume, program_variables.pipR, program_variables.pipL)
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
		
		if user_variables.presenceTermo:
			possible_positions = [1, 6] # This are the only positions we can put the HS if the Thermocycler is present
		else:
			possible_positions = [10, 1, 3] # This order is put on purpose because the position 10 gives the less deck conflict positions
		
		number_hs = math.ceil(number_tubes_mix_hs/number_wells_labware)

		for position in possible_positions:
			try:
				labware_hs = protocol.load_module('heaterShakerModuleV1', position)
				labware_hs.close_labware_latch()
				labware_hs.load_labware(user_variables.APINameLabwareHS, label = f"Eppendorf Rack with Mix on Slot {position}")
				program_variables.deckPositions[position] = "Heater Shaker"
				program_variables.hs_mods[position] = labware_hs
				number_hs -= 1
			except DeckConflictError:
				continue
			
			if number_hs == 0:
				break
			
		# Set the volume sof the mixes in case the HS is present
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
	# We need to calculate it in anouther way, not with number_tubes_needed because it is not an uniform ammoutn of water
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
	coldblocks = setting_labware(number_coldblocks, user_variables.APINameEppendorfPlate, dict(sorted(program_variables.deckPositions.items(),reverse=True)), protocol, label = "Reagents") # We do the inverse deckPositions because it is less likely to have deck conflict error
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
		volWaterPipR, posWaterPipR, volWaterPipL, posWaterPipL = vol_distribute_2pips(program_variables.reactiveWells["Water"]["Volumes Per Tube"][index_tube], wells_distribute_free[well_start:well_start+len(program_variables.reactiveWells["Water"]["Volumes Per Tube"][index_tube])], program_variables.pipR, program_variables.pipL)
		
		well_start += len(program_variables.reactiveWells["Water"]["Volumes Per Tube"][index_tube])
		
		position_tube = program_variables.reactiveWells["Water"]["Positions"][index_tube]
		
		# Transfer with the last pipette if there is some position to distrtiibute with it
		# This part has a lot of optimizing, I think the program could be easier in this part
		if last_pipette_used == program_variables.pipR and posWaterPipR:
			if not last_pipette_used.has_tip:
				check_tip_and_pick(last_pipette_used, program_variables.deckPositions, user_variables, protocol)
			last_pipette_used.distribute(volWaterPipR, position_tube, posWaterPipR, new_tip = "never", touch_tip = True, disposal_volume = 0)
		elif last_pipette_used == program_variables.pipL and posWaterPipL:
			if not last_pipette_used.has_tip:
				check_tip_and_pick(last_pipette_used, program_variables.deckPositions, user_variables, protocol)
			last_pipette_used.distribute(volWaterPipL, position_tube, posWaterPipL, new_tip = "never", touch_tip = True, disposal_volume = 0)
			
		# Transfer with the other pipette
		if last_pipette_used == program_variables.pipR and posWaterPipL:
			if last_pipette_used != None and last_pipette_used.has_tip:
				last_pipette_used.drop_tip()
			check_tip_and_pick(program_variables.pipL, program_variables.deckPositions, user_variables, protocol)
			last_pipette_used = program_variables.pipL
			last_pipette_used.distribute(volWaterPipL, position_tube, posWaterPipL, new_tip = "never", touch_tip = True, disposal_volume = 0)
		elif last_pipette_used == program_variables.pipL and posWaterPipR:
			if last_pipette_used != None and last_pipette_used.has_tip:
				last_pipette_used.drop_tip()
			last_pipette_used = program_variables.pipR
			check_tip_and_pick(program_variables.pipR, program_variables.deckPositions, user_variables, protocol)
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
		optimal_pipette = optimal_pipette_use(program_variables.volTotal, program_variables.pipR, program_variables.pipL)
		wells_distribute_mix = wells_distribute_free[:]
		for index, tube in enumerate(program_variables.mixWells["Positions"]):
			if user_variables.presenceHS == True:
				# Find out in which HS is the tube and shake it
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].set_and_wait_for_shake_speed(user_variables.rpm)
				protocol.delay(seconds=15)
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].deactivate_shaker()
				if optimal_pipette.has_tip == False:
					check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
				optimal_pipette.distribute(float(program_variables.volTotal), tube, wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]], new_tip="never", disposal_volume=0)
			
			else:
				# Mix it with a pipette
				last_pipette = mixing_eppendorf_15(tube, program_variables.volTotalFactor*program_variables.sumSamples, program_variables, user_variables, protocol)
				if optimal_pipette == last_pipette:
					optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]], new_tip="never", disposal_volume=0)
				else:
					last_pipette.drop_tip()
					check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
					optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]], new_tip="never", disposal_volume=0)
					
			del wells_distribute_mix[:program_variables.mixWells["Reactions Per Tube"][index]]
		optimal_pipette.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Distribute DNA parts and acceptor module to the different final wells
	
	generator_final_wells = generator_positions (wells_distribute_free)
	for name_combination, parts_combination in program_variables.combinations.items():
		# Set the final well
		well_final_combination = next(generator_final_wells)
		
		if user_variables.acceptorVolume > 0:
			# Take well where the acceptor is
			optimal_pipette_acceptor = optimal_pipette_use(user_variables.acceptorVolume, program_variables.pipR, program_variables.pipL)
			well_acceptor = find_well_by_value (parts_combination["acceptor"], program_variables.samplePlates)
			# Transfer the acceptor
			check_tip_and_pick (optimal_pipette_acceptor, program_variables.deckPositions, user_variables, protocol)
			optimal_pipette_acceptor.transfer(user_variables.acceptorVolume, well_acceptor, well_final_combination, new_tip = "never")
			optimal_pipette_acceptor.drop_tip()
		
		
		# Transfer all the DNA parts that will contain th efinal constructs
		if user_variables.moduleVolume > 0:
			for part_plasmid in parts_combination["modules"]:
				# Take the module part
				well_source_DNApart = find_well_by_value (part_plasmid, program_variables.samplePlates)
				
				# Transfer the module volume
				optimal_pipette_module = optimal_pipette_use(user_variables.moduleVolume, program_variables.pipR, program_variables.pipL)
				check_tip_and_pick (optimal_pipette_module, program_variables.deckPositions, user_variables, protocol)
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
		run_program_thermocycler(program_variables.tc_mod, user_variables.temperatureProfile, user_variables.temperatureLid, user_variables.finalStateLid, user_variables.finalTemperatureBlock, user_variables.finalVolume, protocol)
	
	# Final home
	protocol.home()
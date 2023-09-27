"""
Python script destined to OT-2
This script performs a merge of samples from N source plates to a lower amount of final plates
This script needs an excel file attached to perform the running
For more info go to https://github.com/Biocomputation-CBGP/LAPrepository/tree/main/LAPEntries,
https://github.com/Biocomputation-CBGP/OT2/tree/main/MergingSamplesSourcePlates and/or
https://www.protocols.io/view/ot-2-protocol-to-transfer-volume-from-several-plat-6qpvr4o62gmk/v1
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
	def __init__(self, general, each_plate, pipettes):
		"""
		This function will take the pandas dataframe that will be the table of the excel variable files
		"""
		self.numberSourcePlates = general[general["Variable Names"] == "Number of Source Plates"]["Value"].values[0]
		self.firstWellSamplePerPlate = list(each_plate[each_plate["Variable Names"] == "First Well Consider Take"].values[0][1:])
		self.volumesSamplesPerPlate = list(each_plate[each_plate["Variable Names"] == "Volume Transfer Sample (uL)"].values[0][1:])
		self.finalMapName = general[general["Variable Names"] == "Name File Final Map"]["Value"].values[0]
		self.wellStartFinalPlate = general[general["Variable Names"] == "Well Start Final Plate"]["Value"].values[0]

		self.volumeReactive = general[general["Variable Names"] == "Volume Reactive Transfer (uL)"]["Value"].values[0]
		self.volumeSample = list(each_plate[each_plate["Variable Names"] == "Volume Transfer Sample (uL)"].values[0][1:])
		self.APINamePipR = pipettes[pipettes["Variable Names"] == "API Name Right Pipette"]["Value"].values[0]
		self.APINamePipL = pipettes[pipettes["Variable Names"] == "API Name Left Pipette"]["Value"].values[0]
		self.replaceTiprack = pipettes[pipettes["Variable Names"] == "Replace Tipracks"]["Value"].values[0]
		
		self.startingTipPipR = pipettes[pipettes["Variable Names"] == "Initial Tip Right Pipette"]["Value"].values[0]
		self.startingTipPipL = pipettes[pipettes["Variable Names"] == "Initial Tip Left Pipette"]["Value"].values[0]
		self.APINameSamplePlate = general[general["Variable Names"] == "API Name Source Plate"]["Value"].values[0]
		self.APINameFinalPlate = general[general["Variable Names"] == "API Name Final Plate"]["Value"].values[0]
		self.APINameFalconPlate = general[general["Variable Names"] == "API Name Rack 15mL Falcon Reactives"]["Value"].values[0]
		self.valueReplaceTiprack = pipettes[pipettes["Variable Names"] == "Replace Tipracks"]["Value"].values[0]
		self.APINameTipR = pipettes[pipettes["Variable Names"] == "API Name Tiprack Right Pipette"]["Value"].values[0]
		self.APINameTipL = pipettes[pipettes["Variable Names"] == "API Name Tiprack Left Pipette"]["Value"].values[0]

		self.nameSheetNameSamples = list(each_plate[each_plate["Variable Names"] == "Name Sheet Map Identifiers"].values[0][1:])
		self.numberSamplesTake = list(each_plate[each_plate["Variable Names"] == "Number Samples Pick"].values[0][1:])
		self.sampleSelection = list(each_plate[each_plate["Variable Names"] == "Type of Sample Selection"].values[0][1:])
		
		
	def check(self, protocol):
		"""
		Function that will check the variables of the Template and will raise errors that will crash the OT run
		It is a validation function of the variables checking errors or inconsistencies
		
		This function is dependant again with the user variabels that we have, some checks are interchangable between protocols, but some of them are specific of the variables
		"""
		
		labware_context = opentrons.protocol_api.labware
		
		# Check is that the minimum variables are present
		if pd.isna([self.finalMapName, self.wellStartFinalPlate, self.APINameSamplePlate, self.APINameFinalPlate]).any():
			raise Exception("Only the variable 'Volume Reactive Transfer (uL)' and 'API Name Rack 15mL Falcon Reactives' can be empty in the Sheet 'GeneralVariables'")

		if (pd.isna(self.volumeReactive) == False and self.volumeReactive > 0) and pd.isna(self.APINameFalconPlate):
			raise Exception("If the variable 'Volume Reactive Transfer (uL)' has a value, the variable 'API Name Rack 15mL Falcon Reactives' needs a value as well")
		
		if pd.isna(self.replaceTiprack):
			raise Exception("The variable 'Replace Tipracks' in the sheet PipetteVariables cannot be left empty")
		
		if not pd.isna(self.APINamePipL) and (pd.isna(self.startingTipPipL) or pd.isna(self.APINameTipL)):
			raise Exception("If 'API Name Left Pipette' is not empty, the variables 'API Name Tiprack Left Pipette' and 'Initial Tip Left Pipette' must be filled")
		if not pd.isna(self.APINamePipR) and (pd.isna(self.startingTipPipR) or pd.isna(self.APINameTipR)):
			raise Exception("If 'API Name Right Pipette' is not empty, the variables 'API Name Tiprack Right Pipette' and 'Initial Tip Right Pipette' must be filled")
		
		if self.replaceTiprack.lower() == "true":
			self.replaceTiprack = True
		elif self.replaceTiprack.lower() == "false":
			self.replaceTiprack = False
		else:
			raise Exception("Replace Tiprack variable value needs to be True or False")
		
		# Check that at least there is 1 pipette
		if pd.isna(self.APINamePipR) and pd.isna(self.APINamePipL):
			raise Exception("We need at least 1 pipette established to perform a protocol")
		
		if pd.isna(self.volumeReactive):
			self.volumeReactive = 0
		if pd.isna(self.numberSourcePlates):
			self.numberSourcePlates = 0
			
		# Check if the numebr of source is more than 1
		if self.numberSourcePlates < 1:
			raise Exception("The variable 'Number of Source Plates' must be equal or greater than 1")
		
		# Check that the source and final plate are realy in the custom_labware namespace
		# If this raises an error some other lines of this function are not going to work, that is why we need to quit the program before and not append it to the errors
		try:
			definition_source_plate = labware_context.get_labware_definition(self.APINameSamplePlate)
			definition_final_plate = labware_context.get_labware_definition(self.APINameFinalPlate)
			
			if self.volumeReactive != 0:
				definition_rack = labware_context.get_labware_definition(self.APINameFalconPlate)

			if pd.isna(self.APINamePipR) == False:
				definition_tiprack_right = labware_context.get_labware_definition(self.APINameTipR)
			if pd.isna(self.APINamePipL) == False:
				definition_tiprack_left = labware_context.get_labware_definition(self.APINameTipL)
		except OSError: # This would be catching the FileNotFoundError that happens when a labware is not found
			raise Exception("One or more of the introduced labwares or tipracks are not in the custom labware directory of the opentrons. Check for any typo of the api labware name.")
		
		# Set that if the pipette is none the other variables are also empty
		if pd.isna(self.APINamePipR):
			self.APINameTipR = None
			self.startingTipPipR = None
			
		if pd.isna(self.APINamePipL):
			self.APINameTipL = None
			self.startingTipPipL = None
		
		# Check that if the tipracks are the same, the initial tips should be ethe same as well
		if not pd.isna(self.APINamePipL) and not pd.isna(self.APINamePipR):
			if self.APINameTipL == self.APINameTipR:
				if self.startingTipPipL != self.startingTipPipR:
					raise Exception("If the tipracks of the right and left mount pipettes are the same, the initial tip should be as well.")
		
		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if len(self.nameSheetNameSamples) < (self.numberSourcePlates) or len(self.sampleSelection) < (self.numberSourcePlates) or len(self.firstWellSamplePerPlate) < (self.numberSourcePlates) or len(self.numberSamplesTake) < (self.numberSourcePlates) or len(self.volumeSample) < (self.numberSourcePlates):
			raise Exception("We need to have at least the same number of plate columns on the Sheet 'PerPlateVariables' as in 'Number DNA Parts Plates'")
		
		if any(pd.isna(elem) == True for elem in self.nameSheetNameSamples[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.nameSheetNameSamples[self.numberSourcePlates:]):
			raise Exception("The values of 'Name Sheet Map Identifiers' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.sampleSelection[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.sampleSelection[self.numberSourcePlates:]):
			raise Exception("The values of 'Type of Sample Selection' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.firstWellSamplePerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.firstWellSamplePerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'First Well Consider Take' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.numberSamplesTake[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.numberSamplesTake[self.numberSourcePlates:]):
			raise Exception("The values of 'Number Samples Pick' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.volumeSample[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.volumeSample[self.numberSourcePlates:]):
			raise Exception("The values of 'Volume Transfer Sample (uL)' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		elif any(elem <= 0 for elem in self.volumeSample[:self.numberSourcePlates]):
			raise Exception("No volume of 'Volume Transfer Sample (uL)' cannot be equal or lower to 0")
		
		# Check if the type of selection variable is one of the established ones
		if any(type_selection.lower() not in ["random","first","last"] for type_selection in self.sampleSelection[:self.numberSourcePlates]):
			raise Exception("One of the 'Type of Sample Selection' not recognised as a valid option. Options are 'random', 'first' and 'last'")
			
		# Check if the number of elements in samples per plate is the same as number of sourc eplates, because if we are not going to take from it, it doesnt make sense to have it in the deck
		if any(number_samples == 0 for number_samples in self.numberSamplesTake):
			raise Exception("You are not taking any samples from one of the source plates")
		
		# Check if there is any typo in the starting tip of both pipettes
		if pd.isna(self.APINamePipR) == False and (self.startingTipPipR not in definition_tiprack_right["groups"][0]["wells"]):
			raise Exception("Starting tip of right pipette is not valid, check for typos")
		if pd.isna(self.APINamePipL) == False and (self.startingTipPipL not in definition_tiprack_left["groups"][0]["wells"]):
			raise Exception("Starting tip of left pipette is not valid, check for typos")
		
		for initial_well_source_plate in self.firstWellSamplePerPlate[:self.numberSourcePlates]:
			if initial_well_source_plate not in list(definition_source_plate["wells"].keys()):
				raise Exception(f"The well '{initial_well_source_plate}' does not exist in the labware {self.APINameSamplePlate}, check for typos")
		
		if self.wellStartFinalPlate not in list(definition_final_plate["wells"].keys()):
			raise Exception(f"The well '{self.wellStartFinalPlate}' does not exist in the labware {self.APINameFinalPlate}, check for typos")
		
		# Check if the volume reactive + sample is greater than the max volume
		first_key = list(labware_context.get_labware_definition(self.APINameFinalPlate)["wells"].keys())[0]
		vol_max_tube = labware_context.get_labware_definition(self.APINameFinalPlate)["wells"][first_key]["totalLiquidVolume"]
		for index_plate, volume_sample in enumerate(self.volumeSample[:self.numberSourcePlates]):
			if volume_sample + self.volumeReactive > vol_max_tube:
				raise Exception (f"The 'Volume Transfer Sample (uL)' of Plate {index_plate+1} + the 'Volume Reactive Transfer (uL)' is greater than the max volume of the final plate")
		
		
		for index_plate, first_well in enumerate(self.firstWellSamplePerPlate[:self.numberSourcePlates]):
			# Check the first well + number samples to take is not > number wells
			if (list(definition_source_plate["wells"]).index(first_well) + self.numberSamplesTake[index_plate] > len(definition_source_plate["wells"])):
				raise Exception(f"Plate {index_plate + 1} cannot start with {first_well} and take {self.numberSamplesTake[index_plate]} samples")
		
		# Check the maps sheets exist
		for map_name in self.nameSheetNameSamples[:self.numberSourcePlates]:
			try:
				map_names = pd.read_excel("/data/user_storage/VariablesMergeSamples.xlsx", engine="openpyxl", sheet_name = map_name, header = None)
				# map_names = pd.read_excel("VariablesMergeSamples.xlsx", engine="openpyxl", sheet_name = map_name, header = None)
			except ValueError: # Error that appears when the sheet 'map_name' does not exist in the excel file
				raise Exception(f"Sheet name of the Map {map_name} does not exist in the excel")
			
			# Check it has the columns and rows according to the labware, less or equal than the labware
			if map_names.shape[0] > len(definition_source_plate["ordering"][0]) or map_names.shape[1] > len(definition_source_plate["ordering"]):
				raise Exception(f"Map {map_name} should have equal or less columns and rows than the labware {self.APINameSamplePlate}. Maps should not have the names of rows and columns, only the values")
		return

class SettedParameters:
	def __init__(self, deck_positions):
		self.sumSamples = 0
		self.pipR = None
		self.pipL = None
		self.samplePlates = {}
		self.finalPlates = {}
		self.reactiveWells = {}
		self.deckPositions = {key: None for key in range(1,deck_positions)}
		self.liquid_samples = None # Initial
		self.liquid_reactive = None # Initial
		self.sameTipRack = None
		
		return
	
	def assign_variables(self, user_variables, protocol):
		self.liquid_samples = protocol.define_liquid(
			name = "Sample",
			description = "Sample that will be inoculated with the selected medium",
			display_color = "#ffbb51"
		)
		
		# Pipette Variables
		if pd.isna(user_variables.APINamePipL) == False:
			self.pipL = protocol.load_instrument(user_variables.APINamePipL, mount = "left")
		if pd.isna(user_variables.APINamePipR) == False:
			self.pipR = protocol.load_instrument(user_variables.APINamePipR, mount = "right")
		
		if user_variables.valueReplaceTiprack.lower() == "true":
			self.replaceTiprack = True
		elif user_variables.valueReplaceTiprack.lower() == "false":
			self.replaceTiprack = False
		
		if user_variables.APINameTipR == user_variables.APINameTipL:
			self.sameTipRack = True
		else:
			self.sameTipRack = False


		# Reactive Variables, if needed
		self.sumSamples = sum(user_variables.numberSamplesTake[:user_variables.numberSourcePlates])
		if pd.isna(user_variables.volumeReactive) == False or user_variables.volumeReactive != 0:
			self.liquid_reactive = protocol.define_liquid(
				name = "Reactive",
				description = "Medium in which the selected colonies will be mixed with",
				display_color = "#6ABFC6"
			)
			self.reactiveWells = {"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples,
								  "Definition Liquid": self.liquid_reactive}
		
		# Final Plate Variables
		# Lets find first how many final plates do we need
		number_wells_final_plate = len(opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["wells"])
		number_source_needed = math.ceil((opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)+self.sumSamples)/number_wells_final_plate)
		for index_plate in range(number_source_needed):
			self.finalPlates[index_plate] = {"Source Plate":index_plate,
											"Position":None,
											"Label":f"Selected Samples Plate {index_plate+1}",
											"Opentrons Place":None,
											"Map Selected Samples":None # We will create this map when we establish the final plate
											}
		
		# Source Plates Definition
		for index_plate in range(user_variables.numberSourcePlates):
			self.samplePlates[index_plate] = {"Number Samples Transfer":user_variables.numberSamplesTake[index_plate],
											  "Position":None,
											  "Label":f"Source Plate {index_plate+1}",
											  "Opentrons Place":None,
											  "Index First Well Sample": opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameSamplePlate)["groups"][0]["wells"].index(user_variables.firstWellSamplePerPlate[index_plate]),
											  "Map Identities": pd.read_excel("/data/user_storage/VariablesMergeSamples.xlsx", sheet_name = user_variables.nameSheetNameSamples[index_plate], engine = "openpyxl", header = None),
											#   "Map Identities": pd.read_excel("VariablesMergeSamples.xlsx", sheet_name = user_variables.nameSheetNameSamples[index_plate], engine = "openpyxl", header = None),
											  "Selected Samples": [], # When we define the labware we will fill this value
											  "Type Selection": user_variables.sampleSelection[index_plate].lower(),
											  "Volume Sample Transfer":user_variables.volumeSample[index_plate]}
		
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
		# self.map.to_csv(name_final_file, header = True, index = True)
		self.map.to_csv("/data/user_storage/"+name_final_file, header = True, index = True)

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

def find_safe_15mLfalcon_height (vol_falcon, theory_position):
	"""
	This function will return the height in which the pipette should aspirate and or dispense the volume to not get wet while doing it
	
	It is manually measured, meaning that if you change the tubes you should test if this work or redo the heights

	This function takes 2 inputs, the tube position and the volume it has and will return the same position with the according height
	"""

	if vol_falcon <= 100: # The values of comparing are volumes (in uL)
		final_position = theory_position.bottom(z=0.7)
	elif vol_falcon > 100 and vol_falcon <= 3000:
		final_position = theory_position.bottom(z=1)
	elif vol_falcon > 3000 and vol_falcon <= 6000:
		final_position = theory_position.bottom(z = 25)
	elif vol_falcon > 6000 and vol_falcon <= 9000:
		final_position = theory_position.bottom(z = 45)
	elif vol_falcon > 9000:
		final_position = theory_position.bottom(z = 65)
	return final_position

def distribute_z_tracking_falcon15ml (pipette_used, vol_source, vol_distribute_well, pos_source, pos_final):
	"""
	Function that will distribute a volume to a a list of positions from a flacon of 15mL tracking the height of the falcon so the pipette does not get wet
	and have enough volume to aspirate

	Th epipette needs to have a tip to perform this function

	This function needs 5 mandatory arguments to run and it returns the volume that the source tube ends up having
	"""

	# Check that there is enough volume to distribute that volume
	if vol_source < len(pos_final)*vol_distribute_well:
		raise Exception(f"Not enough volume in the source tube, {vol_source}uL, to distribute {vol_distribute_well}uL to {len(pos_final)} reactions")
	
	# Check that the pipette has a tip
	if not pipette_used.has_tip:
		raise Exception(f"No tip attached to distribute with {pipette_used}")

	start_position = 0
	while start_position + 1 <= len(pos_final): # Go throught all the positions
		# Calculate how many reactions we can distribute aspirating from the same height
		number_pos_distr = calculate_max_reactions_constant_height_15mLfalcon (pos_source, vol_source, len(pos_final[start_position:]), vol_distribute_well)
		# Set the positions that th epipette is going to be distribute
		position_distribute = pos_final[start_position:start_position+number_pos_distr]
		pipette_used.distribute(vol_distribute_well, find_safe_15mLfalcon_height (vol_source, pos_source), position_distribute, new_tip = "never", disposal_volume = 0)
		# Update the volume of the tube
		vol_source -= number_pos_distr*vol_distribute_well
		# Update the start position of the final wells
		start_position += number_pos_distr
	return vol_source

def calculate_max_reactions_constant_height_15mLfalcon (tube, vol_tube, total_number_reactions, vol_per_reaction):
	"""
	Function that will return how many reactions of a certain volume can be transfered/distribute without changing the height that the pipette can aspirate
	without getting wet and having volume to aspirate

	4 mandatory arguments are needed for this function
	"""

	# Check if there is enough volume in the tube to transfer all the reactions
	if vol_tube < total_number_reactions*vol_per_reaction:
		raise Exception(f"Not enough volume in the source tube, {vol_tube}uL, to distribute {vol_per_reaction}uL to {total_number_reactions} reactions")
	
	react_distr = 0
	
	# Loop adding 1 reaction until the height of aspirate change
	while find_safe_15mLfalcon_height (vol_tube, tube).point == find_safe_15mLfalcon_height (vol_tube-(react_distr*vol_per_reaction), tube).point:
		if react_distr + 1 > total_number_reactions:
			break
		else: # One more reaction can be transfered
			react_distr += 1
	
	return react_distr

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
	excel_variables = pd.read_excel("/data/user_storage/VariablesMergeSamples.xlsx", sheet_name = None, engine = "openpyxl")
	# excel_variables = pd.read_excel("VariablesMergeSamples.xlsx", sheet_name = None, engine = "openpyxl")
	# Let's check that the minimal sheets
	name_sheets = list(excel_variables.keys())

	if not all(item in name_sheets for item in ["GeneralVariables","PerPlateVariables","PipetteVariables"]):
		raise Exception('The Excel file needs to have min the sheets "GeneralVariables","PerPlateVariables","PipetteVariables"\nThey must have those names')
	
	# Check that all variable sheets have the needed columns and variable names
	general_variables = excel_variables.get("GeneralVariables")
	plate_variables = excel_variables.get("PerPlateVariables")
	pip_variables = excel_variables.get("PipetteVariables")

	if not all(item in list(general_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'GeneralVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in general_variables["Variable Names"].values for item in ['API Name Source Plate','API Name Final Plate','API Name Rack 15mL Falcon Reactives','Volume Reactive Transfer (uL)', 'Number of Source Plates', 'Name File Final Map', 'Well Start Final Plate']):
			raise Exception("'GeneralVariables' sheet table needs to have 7 rows with the following names: 'API Name Source Plate','API Name Final Plate','API Name Rack 15mL Falcon Reactives','Volume Reactive Transfer (uL)', 'Number of Source Plates', 'Name File Final Map', 'Well Start Final Plate'")
		
	if "Variable Names" not in list(plate_variables.columns):
		raise Exception("'PerPlateVariables' sheet table needs to have at least 1 column, 'Variable Names'")
	else:
		if not all(item in plate_variables["Variable Names"].values for item in ['Name Sheet Map Identifiers','Type of Sample Selection','First Well Consider Take', 'Number Samples Pick', 'Volume Transfer Sample (uL)']):
			raise Exception("'PerPlateVariables' Sheet table needs to have 6 rows with the following names: 'Name Sheet Map Identifiers','Type of Sample Selection','First Well Consider Take', 'Number Samples Pick', 'Volume Transfer Sample (uL)'")
	
	if not all(item in list(pip_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'PipetteVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in pip_variables["Variable Names"].values for item in ['API Name Right Pipette','API Name Left Pipette','API Name Tiprack Left Pipette','API Name Tiprack Right Pipette', 'Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks']):
			raise Exception("'PipetteVariables' Sheet table needs to have 7 rows with the following names: 'API Name Right Pipette','API Name Left Pipette','API Name Tiprack Left Pipette','API Name Tiprack Right Pipette', 'Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks'")

	user_variables = UserVariables(general_variables, plate_variables, pip_variables)
	user_variables.check(protocol)
	program_variables = SettedParameters(len(protocol.deck))
	program_variables.assign_variables(user_variables, protocol)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Assign the source and final plates into the deck
	labware_source = setting_labware(user_variables.numberSourcePlates, user_variables.APINameSamplePlate, program_variables.deckPositions, protocol, label = "Sample Source Plate")
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_source}
	
	for index_labware, labware in enumerate(labware_source.items()):
		program_variables.samplePlates[index_labware]["Position"] = labware[0]
		program_variables.samplePlates[index_labware]["Opentrons Place"] = labware[1]
	
		# Assign the correct column names and axis to the 'Map Identifiers' after having check that the dimensions are correct with user_variables.check()
		program_variables.samplePlates[index_labware]["Map Identities"].columns = list(labware[1].columns_by_name().keys())[:program_variables.samplePlates[index_labware]["Map Identities"].shape[1]]
		program_variables.samplePlates[index_labware]["Map Identities"].index = list(labware[1].rows_by_name().keys())[:program_variables.samplePlates[index_labware]["Map Identities"].shape[0]]
	
	labware_final = setting_labware(len(program_variables.finalPlates), user_variables.APINameFinalPlate, program_variables.deckPositions, protocol, label = "Final Plate")
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_final}
	
	for index_labware, labware in enumerate(labware_final.items()):
		program_variables.finalPlates[index_labware]["Position"] = labware[0]
		program_variables.finalPlates[index_labware]["Opentrons Place"] = labware[1]
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Set some variables that needed the setting of the labware
	# Set the samples we are transfering from each source plate
	for index_initial_plate, source_plate in program_variables.samplePlates.items():
		# Obtain the list of possible wells to select from
		list_wells_possible_selection = source_plate["Opentrons Place"].wells()[source_plate["Index First Well Sample"]:]
		# Obtain the list of well we cannot select from, which are the ones that have the "-" character
		wells_not_take = source_plate['Map Identities'].isnull().stack()
		# Remove from list_wells_possible_selection the list wells_not_take
		for well in wells_not_take.index:
			if wells_not_take[well] and source_plate["Opentrons Place"].wells_by_name()[f"{well[0]}{well[1]}"] in list_wells_possible_selection:
				list_wells_possible_selection.remove(source_plate["Opentrons Place"].wells_by_name()[f"{well[0]}{well[1]}"])
		
		if len(list_wells_possible_selection) < source_plate["Number Samples Transfer"]:
			raise Exception (f"Not enough wells in Plate {index_initial_plate+1} to choose from to take {source_plate['Number Samples Transfer']} samples")
		
		source_plate["Selected Samples"] = wells_selection(list(list_wells_possible_selection), source_plate["Number Samples Transfer"], source_plate["Type Selection"])
		
		# Let's put volume in the wells that have somethign different to '-'
		all_wells_with_samples = ~source_plate['Map Identities'].isnull().stack()
		for well in all_wells_with_samples.index:
			if all_wells_with_samples[well]:
				source_plate["Opentrons Place"][f"{well[0]}{well[1]}"].load_liquid(liquid = program_variables.liquid_samples, volume = 0.9*list(labware_context.get_labware_definition(user_variables.APINameSamplePlate)["wells"].values())[0]['totalLiquidVolume'])
	
	# Set the maps of the final labware
	for index_final_plate, final_plate in program_variables.finalPlates.items():
		final_plate["Map Selected Samples"] = MapLabware(final_plate["Opentrons Place"])
		
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Set Falcon Rack if needed
	if user_variables.volumeReactive != 0:
		# Find out how many tubes we need
		vol_max_falcon = list(labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"].values())[0]['totalLiquidVolume']
		falcon_needed, program_variables.reactiveWells["Reactions Per Tube"], program_variables.reactiveWells["Volumes"] = number_tubes_needed (user_variables.volumeReactive, program_variables.sumSamples, vol_max_falcon*0.9)
		# Find out how many falcon racks we need
		number_wells_tuberack = len(labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"])
		tuberacks_needed = math.ceil(falcon_needed/number_wells_tuberack)
		# Place falcon labware
		labware_falcons = setting_labware(tuberacks_needed, user_variables.APINameFalconPlate, program_variables.deckPositions, protocol, label = "Reactive Labware")
		program_variables.deckPositions = {**program_variables.deckPositions , **labware_falcons}
		
		# Now we are going to set the reactives in the coldblock positions, we need to keep track of these positions for liquid movement
		# Get the possible positions merging all the labwares from the tuberacks
		positions_tuberack = []
		for labware in labware_falcons.values():
			positions_tuberack += labware.wells()
		generator_positions_reactives = generator_positions(positions_tuberack)
		
		# Assign to each antibiotic the positions of the falcons
		for volume_tube in program_variables.reactiveWells["Volumes"]:
			well_tube_falcon = next(generator_positions_reactives)
			program_variables.reactiveWells["Positions"].append(well_tube_falcon)
			well_tube_falcon.load_liquid(liquid = program_variables.reactiveWells["Definition Liquid"], volume = volume_tube)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Transfer reactives, if neccessary and samples
	
	# First we create the possible final wells where to distribute the reactives and samples
	final_wells = []
	for plate in list(program_variables.finalPlates.values()):
		final_wells += plate["Opentrons Place"].wells()
	index_start_well_final_plate = labware_context.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)
	
	
	# Distribute reactives
	if user_variables.volumeReactive != 0:
		optimal_pipette = give_me_optimal_pipette (user_variables.volumeReactive, program_variables.pipR, program_variables.pipL)
		if optimal_pipette.mount == "right":
			tiprack = user_variables.APINameTipR
			starting_tip = user_variables.startingTipPipR
		else:
			tiprack = user_variables.APINameTipL
			starting_tip = user_variables.startingTipPipL
		
		check_tip_and_pick(optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = starting_tip, same_tiprack = program_variables.sameTipRack)
		wells_distribute_reactive = final_wells[index_start_well_final_plate:index_start_well_final_plate+program_variables.sumSamples]
		for index_tube, tube in enumerate(program_variables.reactiveWells["Reactions Per Tube"]):
			if len(wells_distribute_reactive) <= tube:
				program_variables.reactiveWells["Volumes"][index_tube] = distribute_z_tracking_falcon15ml (optimal_pipette,
												  program_variables.reactiveWells["Volumes"][index_tube],
												  user_variables.volumeReactive,
												  program_variables.reactiveWells["Positions"][index_tube],
												  wells_distribute_reactive)
				tube -= len(wells_distribute_reactive)
			else:
				program_variables.reactiveWells["Volumes"][index_tube] = distribute_z_tracking_falcon15ml (optimal_pipette,
												  program_variables.reactiveWells["Volumes"][index_tube],
												  user_variables.volumeReactive,
												  program_variables.reactiveWells["Positions"][index_tube],
												  wells_distribute_reactive[:tube])
				del wells_distribute_reactive[:tube]
				tube -= len(wells_distribute_reactive)
		optimal_pipette.drop_tip()
		
	# Distribute Samples
	wells_transfer_samples = generator_positions(final_wells[index_start_well_final_plate:index_start_well_final_plate+program_variables.sumSamples])
	for plate in list(program_variables.samplePlates.values()):
		optimal_pipette = give_me_optimal_pipette (plate["Volume Sample Transfer"], program_variables.pipR, program_variables.pipL)
		if optimal_pipette.mount == "right":
			tiprack = user_variables.APINameTipR
			starting_tip = user_variables.startingTipPipR
		else:
			tiprack = user_variables.APINameTipL
			starting_tip = user_variables.startingTipPipL
		
		for sample_well in plate["Selected Samples"]:
			check_tip_and_pick(optimal_pipette, tiprack, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = starting_tip, same_tiprack = program_variables.sameTipRack)
			final_well = next(wells_transfer_samples)
			optimal_pipette.transfer(plate["Volume Sample Transfer"], sample_well, final_well, new_tip="never")
			# Map the transfer
			source_well_name = plate["Map Identities"].iloc[list(plate["Opentrons Place"].rows_by_name().keys()).index(sample_well._core._row_name),list(plate["Opentrons Place"].columns_by_name().keys()).index(sample_well._core._column_name)]
			for final_plate in list(program_variables.finalPlates.values()):
				if final_plate["Opentrons Place"] == final_well._parent:
					final_plate["Map Selected Samples"].assign_value(source_well_name, final_well._core._row_name, final_well._core._column_name)
			# Drop tip
			optimal_pipette.drop_tip()
			
	# Export map(s) in an excel
	writer = pd.ExcelWriter(f'/data/user_storage/{user_variables.finalMapName}.xlsx', engine='openpyxl')
	# writer = pd.ExcelWriter(f'{user_variables.finalMapName}.xlsx', engine='openpyxl')
	
	for final_plate in program_variables.finalPlates.values():
		final_plate["Map Selected Samples"].map.to_excel(writer, sheet_name = f"FinalMapSlot{final_plate['Position']}")
	
	writer.save()
	
	# Final homing
	protocol.home()
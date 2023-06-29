"""
Python script destined to OT-2
This script performs a creation of final plates selecting samples in base of a criteria
This script needs an excel file attached to perform the running
For more info go to https://github.com/Biocomputation-CBGP/LAPrepository/tree/main/LAPEntries,
https://github.com/Biocomputation-CBGP/OT2/tree/main/ColonySelection and/or
https://www.protocols.io/view/ot-2-counter-selection-5qpvor5xdv4o/v1
"""


class UserVariables:
	
	def __init__(self, general, each_plate, pipettes):
		self.numberSourcePlates = general[general["Variables Names"] == "Number of Source Plates"]["Value"].values[0]
		self.nameReactives = general[general["Variables Names"] == "Name Reactives"]["Value"].values[0].replace(" ","").split(",")
		self.APINameSamplePlate = general[general["Variables Names"] == "API Name Source Plate"]["Value"].values[0]
		self.APINameFalconPlate = general[general["Variables Names"] == "API Name Rack 15mL Falcon Reactives"]["Value"].values[0]
		self.APINameFinalPlate = general[general["Variables Names"] == "API Name Final Plate"]["Value"].values[0]
		self.volumesReactivePerPlate = general[general["Variables Names"] == "Volume per Reactive (uL)"]["Value"].values[0].replace(" ","").split(",")
		
		self.APINamePipR = pipettes[pipettes["Variables Names"] == "API Name Right Pipette"]["Value"].values[0]
		self.APINamePipL = pipettes[pipettes["Variables Names"] == "API Name Left Pipette"]["Value"].values[0]
		self.startingTipPipR = pipettes[pipettes["Variables Names"] == "Initial Tip Right Pipette"]["Value"].values[0]
		self.startingTipPipL = pipettes[pipettes["Variables Names"] == "Initial Tip Left Pipette"]["Value"].values[0]
		self.APINameTipR = pipettes[pipettes["Variables Names"] == "API Name Tiprack Right Pipette"]["Value"].values[0]
		self.APINameTipL = pipettes[pipettes["Variables Names"] == "API Name Tiprack Left Pipette"]["Value"].values[0]
		self.replaceTiprack = pipettes[pipettes["Variables Names"] == "Replace Tipracks"]["Value"].values[0]
		
		self.threshold = list(each_plate[each_plate["Variables Names"] == "Threshold Selection Value"].values[0][1:])
		self.reactivesPerPlate = list(each_plate[each_plate["Variables Names"] == "Reactives Per Plate"].values[0][1:])
		self.nameSheetLowerThreshold = list(each_plate[each_plate["Variables Names"] == "Name Sheet Selection Value<Threshold"].values[0][1:])
		self.nameSheetHigherThreshold = list(each_plate[each_plate["Variables Names"] == "Name Sheet Selection Value>Threshold"].values[0][1:])
		self.wellStartFinalPlate = list(each_plate[each_plate["Variables Names"] == "Well Start Final Plate"].values[0][1:])
		
		self.finalMapName = list(each_plate[each_plate["Variables Names"] == "Final Map Name"].values[0][1:])
		self.volumesSamplesPerPlate = list(each_plate[each_plate["Variables Names"] == "Volume Transfer Sample (uL)"].values[0][1:])
		return
		
	def check(self, protocol):
		"""
		Function that will check the variables of the Template and will raise errors that will crash the OT run
		It is a validation function of the variables checking errors or inconsistencies
		
		This function is dependant again with the variabels that we have, some checks are interchangable between protocols, but some of them are specific of the variables
		"""
		
		labware_context = opentrons.protocol_api.labware
		
		if self.replaceTiprack.lower() == "true":
			self.replaceTiprack = True
		elif self.replaceTiprack.lower() == "false":
			self.replaceTiprack = False
		else:
			raise exception("Replace Tiprack variable value needs to be True or False")
		
		try:
			definition_source_plate = labware_context.get_labware_definition(self.APINameSamplePlate)
			definition_final_plate = labware_context.get_labware_definition(self.APINameFinalPlate)
			definition_rack = labware_context.get_labware_definition(self.APINameFalconPlate)
			if pd.isna(self.APINamePipR) == False:
				definition_tiprack_right = labware_context.get_labware_definition(self.APINameTipR)
			if pd.isna(self.APINamePipL) == False:
				definition_tiprack_left = labware_context.get_labware_definition(self.APINameTipL)
		except:
			raise Exception("One or more of the introduced labwares or tipracks are not in the labware directory of the opentrons. Check for any typo of the api labware name.")
		
		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if any(pd.isna(elem) == True for elem in self.threshold[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.threshold[self.numberSourcePlates:]):
			raise Exception("The values of 'Threshold Selection Value' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.nameSheetLowerThreshold[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.nameSheetLowerThreshold[self.numberSourcePlates:]):
			raise Exception("The values of 'Name Sheet Selection Value<Threshold' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.nameSheetHigherThreshold[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.nameSheetHigherThreshold[self.numberSourcePlates:]):
			raise Exception("The values of 'Name Sheet Selection Value>Threshold' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.reactivesPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.reactivesPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Reactives Per Plate' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.wellStartFinalPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.wellStartFinalPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Well Start Final Plate' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.finalMapName[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.finalMapName[self.numberSourcePlates:]):
			raise Exception("The values of 'Final Map Name' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.volumesSamplesPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.volumesSamplesPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Volume Transfer Sample (uL)' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		
		# Check if the sheet names for the selection values exist and if they fit the labware source description
		for sheet_name_lowerThreshold in self.nameSheetLowerThreshold[:self.numberSourcePlates]:
			try:
				values_lower = pd.read_excel("/data/user_storage/VariablesCounterSelection.xlsx", sheet_name = sheet_name_lowerThreshold, engine = "openpyxl", header = None)
			except:
				raise Exception(f"Sheet Name {sheet_name_lowerThreshold} does not exist in excel file")
			if values_lower.shape[0] != len(definition_source_plate["ordering"][0]) or values_lower.shape[1] != len(definition_source_plate["ordering"]):
				raise Exception(f"Selecting Sheet Values should have the dimension of the source labware ({len(definition_source_plate['ordering'][0])} rows and {len(definition_source_plate['ordering'])} columns).\nDo not include the names of the rows or the columns in the sheet, only values.")
			
		for sheet_name_higherThreshold in self.nameSheetHigherThreshold[:self.numberSourcePlates]:
			try:
				# values_higher = pd.read_excel("C:\\Users\\Ana_CBGP\\Documentos\\app_\\scripts_subir\\VariablesCounterSelection.xlsx", sheet_name = sheet_name_higherThreshold, engine = "openpyxl", header = None)
				values_higher = pd.read_excel("/data/user_storage/VariablesCounterSelection.xlsx", sheet_name = sheet_name_higherThreshold, engine = "openpyxl", header = None)
			except:
				raise Exception(f"Sheet Name {sheet_name_lowerThreshold} does not exist in excel file")
			
			if values_higher.shape[0] != len(definition_source_plate["ordering"][0]) or values_higher.shape[1] != len(definition_source_plate["ordering"]):
				raise Exception(f"Selecting Sheet Values should have the dimension of the source labware ({len(definition_source_plate['ordering'][0])} rows and {len(definition_source_plate['ordering'])} columns).\nDo not include the names of the rows or the columns in the sheet, only values.")
		
		# Check if there is any typo in the starting tip of both pipettes
		if pd.isna(self.APINamePipR) == False and (self.startingTipPipR not in definition_tiprack_right["groups"][0]["wells"]):
			raise Exception("Starting tip of right pipette is not valid, check for typos")
		if pd.isna(self.APINamePipL) == False and (self.startingTipPipL not in definition_tiprack_left["groups"][0]["wells"]):
			raise Exception("Starting tip of left pipette is not valid, check for typos")
			
		# Check if the well of the starting plate exist in the final labware
		for index_labware in range(self.numberSourcePlates):
			vol_sample_needed = len(self.reactivesPerPlate[index_labware].split(","))*self.volumesSamplesPerPlate[index_labware]
			if float(list(definition_source_plate["wells"].values())[0]['totalLiquidVolume']) < vol_sample_needed:
				raise Exception(f"Volume of Sample needed in Source Plate {index_labware+1} is greater than the max volume of a well in that labware")

		return
	
class SettedParameters:
	
	def __init__(self):
		self.numberReactives = 0
		self.pipR = None
		self.pipL = None
		self.sameTiprack = None
		self.samplePlates = {}
		self.finalPlates = {}
		self.reactiveWells = {}
		self.deckPositions = {key: None for key in range(1,12)}
		self.colors_mediums = ["#ffbb51"] # Initial filled with the one color of the sample
		self.liquid_samples = None # Initial
		return
	
	def assign_variables(self, user_variables, protocol):
		self.liquid_samples = protocol.define_liquid(
			name = "Sample",
			description = "Sample that will be inoculated with the selected medium",
			display_color = "#ffbb51"
		)
		
		self.numberReactives = len(user_variables.nameReactives)
		
		# Pipette Variables
		if pd.isna(user_variables.APINamePipR) == False:
			self.pipR = protocol.load_instrument(user_variables.APINamePipR, mount = "right")
			if self.pipR.channels != 1:
				raise Exception("Both Right Mount Pipette and Left Mount pipette have to be single channel")
		if pd.isna(user_variables.APINamePipL) == False:
			self.pipL = protocol.load_instrument(user_variables.APINamePipL, mount = "left")
			if self.pipL.channels != 1:
				raise Exception("Both Right Mount Pipette and Left Mount pipette have to be single channel")
		
		# Reactive Tubes
		for index_reactive, reactive in enumerate(user_variables.nameReactives):
			self.reactiveWells[reactive] = {"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":0, "Definition Liquid": None, "Volume Per Sample":float(user_variables.volumesReactivePerPlate[index_reactive])}
			
			while True:
				color_liquid = f"#{random.randint(0, 0xFFFFFF):06x}"
				if color_liquid.lower() != "#ffbb51" and color_liquid.lower() not in self.colors_mediums:
					self.reactiveWells[reactive]["Definition Liquid"] = protocol.define_liquid(
						name = f"{reactive}",
						description = f"Medium {reactive}",
						display_color = color_liquid
					)
					self.colors_mediums.append(color_liquid)
					break
				
		# Source Plates
		incubation_plates_needed = 0
		for index_plate in range(user_variables.numberSourcePlates):
			self.samplePlates[index_plate] = {"Position":None,
											  "Label":f"Source Plate {index_plate+1}",
											  "Mediums":user_variables.reactivesPerPlate[index_plate].replace(" ","").split(","),
											  "Opentrons Place":None,
											  "Values for Selection (Lower than Threshold)":pd.read_excel("/data/user_storage/VariablesCounterSelection.xlsx", sheet_name = user_variables.nameSheetLowerThreshold[index_plate], engine = "openpyxl", header = None),
											  "Values for Selection (Greater than Threshold)":pd.read_excel("/data/user_storage/VariablesCounterSelection.xlsx", sheet_name = user_variables.nameSheetHigherThreshold[index_plate], engine = "openpyxl", header = None),
											  "Threshold Value":user_variables.threshold[index_plate],
											  "Map Selected Colonies":None, # We will create this map when we establish the final plates
											  "Name Final Map":user_variables.finalMapName[index_plate],
											  "Selected Colonies": [],
											  "Volume Transfer Sample":float(user_variables.volumesSamplesPerPlate[index_plate])}
			
			# Incubation Plates
			for reactive_source_plate in self.samplePlates[index_plate]["Mediums"]:
				# Initialize with the values that we can set now
				self.finalPlates[incubation_plates_needed] = {"Source Plate":index_plate,
														   "Position":None,
														   "Label":f"Selected Samples from Plate {index_plate+1} with {reactive_source_plate}",
														   "Medium":reactive_source_plate,
														   "Number Samples":None, # We will have to select and see how many
														   "Opentrons Place":None,
														   "Index Well Start":list(opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["wells"].keys()).index(user_variables.wellStartFinalPlate[index_plate])}
				incubation_plates_needed += 1
				
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

# Functions definitions
# ----------------------------------
# ----------------------------------

def setting_labware (number_labware, labware_name, positions, protocol, label = None):
	"""
	In this function we will set how many labwares we need of every category (source labwares, final, coldblocks, falcon tube racks, etc)
	
	This function will only set the labwares in the different slots of the deck, with not calculate how many we need,
	this way we do not have to change this function and only change the setting_labware function from protocol to protocol
	"""
	try:
		position_plates = [position for position, labware in positions.items() if labware == None] # We obtain the positions in which there are not labwares
		all_plates = {}
		for i in range (number_labware):
			if label == None:
				plate = protocol.load_labware(labware_name, position_plates[i])
			elif type(label) == str:
				plate = protocol.load_labware(labware_name, position_plates[i], label = f"{label} {i+1}")
			elif type(label) == list:
				plate = protocol.load_labware(labware_name, position_plates[i], label = f"{label[i]}")
			all_plates[position_plates[i]] = plate
		return all_plates
	
	except: # There were not enough items in the position_plate to fit the number of labwares that we needed
		raise Exception("There is not enough space in the deck for this protocol, try less samples")



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

def position_dispense_aspirate_falcon15ml (vol_falcon, theory_position):
	"""
	This function will return the height in which the pipette should aspirate the volume
	
	It is manually measured, meaning that if you change the tubes you should test if this work or redo the heights
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
	This function will distribute from a pos_source to pos_final (list) taking in account the height of aspiration of the 15mL falcon tube,
	this way the pipette will not get wet during the transfering of liquids
	
	This function is mainly design to distribute reactives to a plate making less pipette movements with the same pipette because the volume to distribute is the same
	"""
	
	while len(pos_final) != 0: # This will go on until there are no elements in the list pos_final (there are no more positions to transfer reactives to)
		# We are going to compare the height before and after aspirating
		if position_dispense_aspirate_falcon15ml(vol_source, pos_source).point == position_dispense_aspirate_falcon15ml((vol_source-(len(pos_final)*vol_distribute_well)), pos_source).point:
			# Heights are the same, so we are going to take the whole volume and distribute it
			pipette_used.distribute(vol_distribute_well, position_dispense_aspirate_falcon15ml(vol_source, pos_source), pos_final, new_tip = "never", disposal_volume = 0)
			vol_source -= vol_distribute_well*len(pos_final)
			pos_final = []
		
		else:
			# Heights are not the same so we are going to take the maximum, distribute it, change the height and then distribute the rest
			pos_final_original = pos_final
			for number_positions in range(1, len(pos_final_original)+1):
				vol_needed = vol_distribute_well*len(pos_final[:number_positions])
				if position_dispense_aspirate_falcon15ml (vol_source, pos_source) == position_dispense_aspirate_falcon15ml ((vol_source-vol_needed), pos_source):
					next
				else:
					pipette_used.distribute(vol_distribute_well, position_dispense_aspirate_falcon15ml(vol_source, pos_source), pos_final[:number_positions], new_tip = "never", disposal_volume = 0)
					# If you change the disposal volume you need to take it in account when you are calculating the number of tubes
					vol_source -= vol_distribute_well*len(pos_final[:number_positions])
					pos_final = pos_final[number_positions:]
					break
	return

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
	except:
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
		except:
			raise Exception(f"Due to conflicts of space we cannot place {tiprack_name} in the deck")
		
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


def optimal_pipette_use(aVolume, pipette_r, pipette_l):
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
			raise Exception("Volume cannot be picked with pipette(s) associated. Try another pipette combination")
			
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
			raise Exception("Volume cannot be picked with pipette(s) associated. try another pipette combination")
			# Error control
	return

# Body of the Program
# ----------------------------------
# ----------------------------------

import opentrons
import pandas as pd
import random
import math
import numpy as np
from opentrons.motion_planning.deck_conflict import DeckConflictError #in version 2.14
		
metadata = {
'apiLevel':'2.14'
}

def run(protocol:opentrons.protocol_api.ProtocolContext):
	labware_context = opentrons.protocol_api.labware
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Read Variables Excel, define the user and protocol variables and check them for initial errors
	
	excel_variables = pd.read_excel("/data/user_storage/VariablesCounterSelection.xlsx", sheet_name = ["GeneralVariables","PerPlateVariables","PipetteVariables"], engine = "openpyxl")
	user_variables = UserVariables(excel_variables.get("GeneralVariables"),excel_variables.get("PerPlateVariables"),excel_variables.get("PipetteVariables"))
	user_variables.check(protocol)
	program_variables = SettedParameters()
	program_variables.assign_variables(user_variables, protocol)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Set the source and final plates because we know how much we have of both
	source_plates = setting_labware(user_variables.numberSourcePlates, user_variables.APINameSamplePlate, program_variables.deckPositions, protocol, label = "Sample Souce Plate")
	program_variables.deckPositions = {**program_variables.deckPositions , **source_plates}
	vol_max_well_source_labware = list(labware_context.get_labware_definition(user_variables.APINameSamplePlate)["wells"].values())[0]['totalLiquidVolume']
	for index_labware, labware in enumerate(source_plates.items()):
		program_variables.samplePlates[index_labware]["Position"] = labware[0]
		program_variables.samplePlates[index_labware]["Opentrons Place"] = labware[1]
		# program_variables.samplePlates[index_labware]["Map Selected Colonies"] = MapLabware(labware[1])
		
		# Set the liquid of samples
		for well in program_variables.samplePlates[index_labware]["Opentrons Place"].wells():
			well.load_liquid(program_variables.liquid_samples, volume = 0.9*vol_max_well_source_labware)
	
	for index_plate, plate in program_variables.finalPlates.items():
		final_plate = setting_labware(1, user_variables.APINameFinalPlate, program_variables.deckPositions, protocol, label = plate["Label"])
		program_variables.deckPositions = {**program_variables.deckPositions , **final_plate}
		plate["Position"] = list(final_plate.keys())[0]
		plate["Opentrons Place"] = list(final_plate.values())[0]
		program_variables.samplePlates[plate['Source Plate']]["Map Selected Colonies"] = MapLabware(list(final_plate.values())[0]) # It will get done more than once for every source plate but at the end the creation of the labware will be the needed one
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Select which colonies are going to be selected
	for index_plate, plate_source in enumerate(program_variables.samplePlates.values()):
		for index_column in range(len(plate_source["Opentrons Place"].columns())): # Go through columns
			for index_row in range(len(plate_source["Opentrons Place"].rows())): # Go through rows
				# Check if the values are according to the threshold that it was set
				if plate_source['Values for Selection (Lower than Threshold)'].iloc[index_row, index_column] <= plate_source["Threshold Value"] and plate_source['Values for Selection (Greater than Threshold)'].iloc[index_row, index_column] >= plate_source["Threshold Value"]:
					plate_source["Selected Colonies"].append([index_row, index_column])
		# Let's check if the numebr of selected colonies fit in the final labware given the first well in which it should be placed the first selected colony
		if len(plate_source["Selected Colonies"])+list(plate_source["Opentrons Place"].wells_by_name().keys()).index(user_variables.wellStartFinalPlate[index_plate]) > len(list(plate_source["Opentrons Place"].wells_by_name().keys())):
			raise Exception(f"There are {len(plate_source['Selected Colonies'])} samples in {plate_source['Label']} that fulfill the parameters given but they do not fit in the final plate given the start well provided")
	
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Define mediums and their wells
	# First we need to know how many reactions each medium will have
	for labware_final in program_variables.finalPlates.values():
		program_variables.reactiveWells[labware_final["Medium"]]["Number Total Reactions"] += len(program_variables.samplePlates[labware_final["Source Plate"]]["Selected Colonies"])
		labware_final["Number Samples"] = len(program_variables.samplePlates[labware_final["Source Plate"]]["Selected Colonies"])
	
	
	# We need to know the max reactive tube volume
	# For that we need to know the maximum volume of the tubes and how many tubes of the reactives we need in total
	first_key = list(labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"].keys())[0]
	max_volume_well = labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"][first_key]["totalLiquidVolume"]
	
	total_falcons_medium = 0 # Initialize
	for reactive_type in program_variables.reactiveWells.keys():
		number_tubes, program_variables.reactiveWells[reactive_type]["Reactions Per Tube"], program_variables.reactiveWells[reactive_type]["Volumes"] = number_tubes_needed(program_variables.reactiveWells[reactive_type]["Volume Per Sample"], program_variables.reactiveWells[reactive_type]["Number Total Reactions"], 0.9*max_volume_well)
		# The 0.9 max well volume is only to not overfill the volume and give space to put more liquid so the pipetting is assure
		total_falcons_medium += number_tubes
	
	# Set how many tuberacks now that we now how many tubes of antibiotic we need
	number_wells_tuberack = len(labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"])
	tuberacks_needed = math.ceil(total_falcons_medium/number_wells_tuberack)
	
	labware_falcons = setting_labware(tuberacks_needed, user_variables.APINameFalconPlate, program_variables.deckPositions, protocol, label = "Reactive Labware")
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_falcons}
	
	
	# Now we are going to set the reactives in the coldblock positions, we need to keep track of these positions for liquid movement
	# Get the possible positions merging all the labwares from the tuberacks
	positions_tuberack = []
	for labware in labware_falcons.values():
		positions_tuberack += labware.wells()
	generator_positions_reactives = generator_positions(positions_tuberack)
	
	# Assign to each antibiotic the positions of the falcons
	for reactive_type in program_variables.reactiveWells.keys():
		for volume_tube in program_variables.reactiveWells[reactive_type]["Volumes"]:
			well_tube_falcon = next(generator_positions_reactives)
			program_variables.reactiveWells[reactive_type]["Positions"].append(well_tube_falcon)
			well_tube_falcon.load_liquid(liquid = program_variables.reactiveWells[reactive_type]["Definition Liquid"], volume = volume_tube)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Transfer the reactives to their plates
	
	for reactive_type in program_variables.reactiveWells.keys():
		optimal_pipette = optimal_pipette_use(program_variables.reactiveWells[reactive_type]["Volume Per Sample"], program_variables.pipR, program_variables.pipL)
		check_tip_and_pick(optimal_pipette, program_variables.deckPositions, user_variables, protocol)
		wells_distribute_reactive = []
		for number_plate, plate_incubation in program_variables.finalPlates.items():
			if plate_incubation["Medium"] == reactive_type:
				wells_distribute_reactive += plate_incubation["Opentrons Place"].wells()[plate_incubation["Index Well Start"]:plate_incubation["Index Well Start"]+plate_incubation["Number Samples"]]
		for index_tube, tube in enumerate(program_variables.reactiveWells[reactive_type]["Reactions Per Tube"]):
			if len(wells_distribute_reactive) <= tube:
				distribute_z_tracking_falcon15ml (optimal_pipette,
												  program_variables.reactiveWells[reactive_type]["Volumes"][index_tube],
												  program_variables.reactiveWells[reactive_type]["Volume Per Sample"],
												  program_variables.reactiveWells[reactive_type]["Positions"][index_tube],
												  wells_distribute_reactive)
				tube -= len(wells_distribute_reactive)
				program_variables.reactiveWells[reactive_type]["Volumes"][index_tube] -= len(wells_distribute_reactive)*program_variables.reactiveWells[reactive_type]["Volume Per Sample"]
			else:
				distribute_z_tracking_falcon15ml (optimal_pipette,
												  program_variables.reactiveWells[reactive_type]["Volumes"][index_tube],
												  program_variables.reactiveWells[reactive_type]["Volume Per Sample"],
												  program_variables.reactiveWells[reactive_type]["Positions"][index_tube],
												  wells_distribute_reactive[:tube])
				del wells_distribute_reactive[:tube]
				tube -= len(wells_distribute_reactive)
				program_variables.reactiveWells[reactive_type]["Volumes"][index_tube] -= len(wells_distribute_reactive)*program_variables.reactiveWells[reactive_type]["Volume Per Sample"]
		optimal_pipette.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Transfer the samples to their plates
	for final_plate in program_variables.finalPlates.values():
		optimal_pipette = optimal_pipette_use(program_variables.samplePlates[final_plate["Source Plate"]]["Volume Transfer Sample"], program_variables.pipR, program_variables.pipL)
		source_plate = program_variables.samplePlates[final_plate["Source Plate"]]["Opentrons Place"]
		selected_colonies = program_variables.samplePlates[final_plate["Source Plate"]]["Selected Colonies"] # each item is [index_rows, index_column]
		wells_transfer_samples = generator_positions(final_plate["Opentrons Place"].wells()[final_plate["Index Well Start"]:final_plate["Index Well Start"]+final_plate["Number Samples"]])
		
		for colony_transfer in selected_colonies:
			check_tip_and_pick(optimal_pipette, program_variables.deckPositions, user_variables, protocol)
			well_final = next(wells_transfer_samples)
			well_source = list(source_plate.rows_by_name())[colony_transfer[0]]+list(source_plate.columns_by_name())[colony_transfer[1]]
			optimal_pipette.transfer(program_variables.samplePlates[final_plate["Source Plate"]]["Volume Transfer Sample"],
									source_plate[well_source],
									well_final,
									new_tip="never")
			optimal_pipette.drop_tip()

			# Assign value to the map of the source plate
			program_variables.samplePlates[final_plate["Source Plate"]]["Map Selected Colonies"].assign_value(f"{well_source} from {program_variables.samplePlates[final_plate['Source Plate']]['Label']}", well_final._core._row_name, well_final._core._column_name)
		
		# Export the source plate map
		program_variables.samplePlates[final_plate["Source Plate"]]["Map Selected Colonies"].export_map(f'{program_variables.samplePlates[final_plate["Source Plate"]]["Name Final Map"]}.csv')
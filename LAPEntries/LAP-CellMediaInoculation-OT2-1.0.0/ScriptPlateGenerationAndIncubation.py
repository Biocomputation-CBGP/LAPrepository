"""
Python script destined to OT-2
This script performs a creation of reactive plates mixed with the respective colonies of the source plate
This script needs a csv attached to perform the running and will give an output file (txt) with some instructions
For more info go to https://github.com/Biocomputation-CBGP/LAPrepository/tree/main/LAPEntries,
https://github.com/Biocomputation-CBGP/OT2/tree/main/AntibioticPlatesGeneration and/or
https://www.protocols.io/view/ot-2-media-dispensing-and-culture-inoculation-prot-q26g7yb3kgwz/v1
"""

## Packages needed for the running of the protocol
import opentrons
import pandas as pd
import math
import random
from opentrons.motion_planning.deck_conflict import DeckConflictError #in version 6.3.1
from opentrons.protocol_api.labware import OutOfTipsError # in version 6.3.1

# Classes definitions
# ----------------------------------
# ----------------------------------

class UserVariables:
	"""
	Class that will contain the parameters setted in the variables csv and will process them to work easily in the rest of the protocol
	The coding of this function is dependant of the variables in the Template of the protocol and the names have to be consistent with the rest of the code
	"""
	def __init__(self, general, each_plate, pipettes):
		"""
		This function will take the pandas dataframe that will be the table of the excel variable files
		"""
		self.numberSourcePlates = general[general["Variable Names"] == "Number of Source Plates"]["Value"].values[0]
		self.samplesPerPlate = list(each_plate[each_plate["Variable Names"] == "Samples per plate"].values[0][1:])
		self.firstWellSamplePerPlate = list(each_plate[each_plate["Variable Names"] == "First Well With Sample"].values[0][1:])
		self.nameAntibiotics = general[general["Variable Names"] == "Name Medias"]["Value"].values[0]

		self.volumeAntibiotic = general[general["Variable Names"] == "Volume of Media to Transfer (uL)"]["Value"].values[0]
		self.volumeSample = general[general["Variable Names"] == "Volume of Sample to Transfer (uL)"]["Value"].values[0]
		self.APINamePipR = pipettes[pipettes["Variable Names"] == "Name Right Pipette (Multichannel)"]["Value"].values[0]
		self.APINamePipL = pipettes[pipettes["Variable Names"] == "Name Left Pipette (Singlechannel)"]["Value"].values[0]
		
		self.startingTipPipR = pipettes[pipettes["Variable Names"] == "Initial Tip Right Pipette"]["Value"].values[0]
		self.startingTipPipL = pipettes[pipettes["Variable Names"] == "Initial Tip Left Pipette"]["Value"].values[0]
		self.APINameSamplePlate = general[general["Variable Names"] == "Name Source Plate"]["Value"].values[0]
		self.APINameIncubationPlate = general[general["Variable Names"] == "Name Final Plate"]["Value"].values[0]
		self.APINameFalconPlate = general[general["Variable Names"] == "Name 15mL Tuberack"]["Value"].values[0]
		self.valueReplaceTiprack = pipettes[pipettes["Variable Names"] == "Replace Tipracks"]["Value"].values[0]
		self.APINameTipR = pipettes[pipettes["Variable Names"] == "API Name Right Pipette TipRack"]["Value"].values[0]
		self.APINameTipL = pipettes[pipettes["Variable Names"] == "API Name Left Pipette TipRack"]["Value"].values[0]
		
		self.antibioticsPerPlate = list(each_plate[each_plate["Variable Names"] == "Media(s) per plate"].values[0][1:])
		
		self.replaceTiprack = pipettes[pipettes["Variable Names"] == "Replace Tipracks"]["Value"].values[0]
		
		return
	
	def check(self, protocol):
		"""
		Function that will check the variables of the Template and will raise errors that will crash the OT run
		It is a validation function of the variables checking errors or inconsistencies
		
		This function is dependant again with the variabels that we have, some checks are interchangable between protocols, but some of them are specific of the variables
		"""
		
		labware_context = opentrons.protocol_api.labware
		
		# Check none of the values are empty
		if any(pd.isna(element) for element in [self.numberSourcePlates, self.nameAntibiotics, self.volumeAntibiotic, self.volumeSample, self.APINamePipR, self.APINamePipL, self.startingTipPipR, self.startingTipPipL, self.APINameSamplePlate, self.APINameIncubationPlate, self.APINameFalconPlate, self.valueReplaceTiprack, self.APINameTipR, self.APINameTipL, self.replaceTiprack]):
			raise Exception("None of the cells in the sheets 'GeneralVariables' and 'PipetteVariables' can be left empty")
		else:
			self.nameAntibiotics = self.nameAntibiotics.replace(" ","").split(",")
			self.valueReplaceTiprack =self.valueReplaceTiprack.lower()
		if all(pd.isna(element) for element in self.samplesPerPlate):
			raise Exception("The Variable 'Samples per plate' cannot be left completely empty, it is necessary to have as many values as the value in 'Number of Source Plates'")
		if all(pd.isna(element) for element in self.firstWellSamplePerPlate):
			raise Exception("The Variable 'First Well With Sample' cannot be left completely empty, it is necessary to have as many values as the value in 'Number of Source Plates'")
		if all(pd.isna(element) for element in self.antibioticsPerPlate):
			raise Exception("The Variable 'Media(s) per plate' cannot be left completely empty, it is necessary to have as many values as the value in 'Number of Source Plates'")
		
		# Check that the source and final plate are realy in the custom_labware namespace
		# If this raises an error some other lines of this function are not going to work, that is why we need to quit the program before and not append it to the errors
		try:
			definition_source_plate = labware_context.get_labware_definition(self.APINameSamplePlate)
			definition_final_plate = labware_context.get_labware_definition(self.APINameIncubationPlate)
			definition_rack = labware_context.get_labware_definition(self.APINameFalconPlate)
			definition_tiprack_right = labware_context.get_labware_definition(self.APINameTipR)
			definition_tiprack_left = labware_context.get_labware_definition(self.APINameTipL)
		except OSError: # This would be catching the FileNotFoundError that happens when a labware is not found
			raise Exception("One or more of the introduced labwares or tipracks are not in the custom labware directory of the opentrons. Check for any typo of the api labware name.")
		
		# Check that we have at least 1 source plate
		if self.numberSourcePlates <= 0:
			raise Exception("We need at least 1 source plate to perform the protocol")

		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if any(pd.isna(elem) == True for elem in self.samplesPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.samplesPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Samples per plate' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.firstWellSamplePerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.firstWellSamplePerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'First Well With Sample' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.antibioticsPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.antibioticsPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Antibiotic per plate' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		
		# We are going to check that the number of cells in each plate is not larger than the capacity of the source plates
		for number_plate, number_cells_per_plate in enumerate(self.samplesPerPlate):
			if type(number_cells_per_plate) != int and number_plate < self.numberSourcePlates:
				raise Exception("Every cell of Samples per plate has to be a number or an empty cell")
			if len(definition_source_plate["wells"]) < number_cells_per_plate:
				raise Exception("Number of cells is larger than the capacity of the source plate labware")
			
			if (number_plate < self.numberSourcePlates and pd.isna(self.antibioticsPerPlate[number_plate])) or (number_plate >= self.numberSourcePlates and not pd.isna(self.antibioticsPerPlate[number_plate])):
				raise Exception("Antibiotic per plate have to be filled consecutivelly and from Plate 1 to number of source plates")
		
		# Because we need both pipettes, a multichannel and a singlechannel we are going to check that both are provided
		# We are going to check if they have the appropiate channels after defining the pipettes
		if self.APINamePipL.lower() in ["none","-"] or pd.isna(self.APINamePipL) or pd.isna(self.APINamePipR) or self.APINamePipR.lower in ["none","-"]:
			raise Exception ("We need 2 pipettes: a multichannel in the right mount and a singlechannel in the left mount")
		
		# We are going to check that the colonies + antibiotic is not more than the max volume of the wells in the final plates
		max_volume_well = float(list(definition_final_plate["wells"].values())[0]['totalLiquidVolume'])
		if self.volumeAntibiotic + self.volumeSample > max_volume_well:
			raise Exception("The sum of sample and antibiotic volumes exceeds the max volume of final plate wells")
		
		# We are going to check that the source and final plates have same dimensions (rows and columns)
		rows_source = len(definition_source_plate["ordering"][0])
		rows_final = len(definition_final_plate["ordering"][0])
		
		if rows_source != rows_final: # We need to have the same ammount of rows but not the same ammount of columns
			raise Exception("Source and final plates have not same number of rows")
		else:
			pass
		
		# We are going to check if the numer of indexes in antibiotics per plate is the same as number of Name antibiotics
		all_plates_antibiotics = ",".join(self.antibioticsPerPlate[:self.numberSourcePlates]).replace(" ","").split(",")
		all_plates_antibiotics = list(dict.fromkeys(all_plates_antibiotics))
		if all(antibiotic in self.nameAntibiotics for antibiotic in all_plates_antibiotics) == False:
			raise Exception(f"The following antibiotic(s) are not defined in variable 'Name Antibiotics': {set(all_plates_antibiotics)-set(self.nameAntibiotics)}")
		if all(antibiotic in all_plates_antibiotics for antibiotic in self.nameAntibiotics) == False:
			raise Exception(f"The following antibiotic(s) are not being used: {set(self.nameAntibiotics)-set(all_plates_antibiotics)}")
		
		# Check that if the tipracks are the same, the initial tips should be ethe same as well
		if not pd.isna(self.APINamePipL) and not pd.isna(self.APINamePipR):
			if self.APINameTipL == self.APINameTipR:
				if self.startingTipPipL != self.startingTipPipR:
					raise Exception("If the tipracks of the right and left mount pipettes are the same, the initial tip should be as well.")
		
		# Control of typos in the initial tip both of right pipette and left pipette, i.e., check if that tip exist
		if self.startingTipPipR not in definition_tiprack_right["groups"][0]["wells"]:
			raise Exception("Starting tip of right pipette is not valid, check for typos")
		if self.startingTipPipL not in definition_tiprack_left["groups"][0]["wells"]:
			raise Exception("Starting tip of left pipette is not valid, check for typos")
		
		# Control that the multipipette actually starts at A and not other letter, in general that starts with the first place of the column in the tiprack
		# This can only be checked correctly if the tip actually exists
		if self.startingTipPipR.lower() not in list(column[0].lower() for column in definition_tiprack_right["ordering"]):
			# Check that has to be A in the multichannel
			raise Exception("The initial tip of the multichannel pipette needs to be at the top of the column, e.g., it has to start with an A")
		
		if self.replaceTiprack.lower() == "false":
			self.replaceTiprack = False
		elif self.replaceTiprack.lower() == "true":
			self.replaceTiprack = True
		else:
			raise Exception("Replace Tiprack variable value needs to be True or False")
		
		# Check that the initial well with sample exist in the labware source
		for initial_well_source_plate in self.firstWellSamplePerPlate[:self.numberSourcePlates]:
			if initial_well_source_plate not in list(definition_source_plate["wells"].keys()):
				raise Exception(f"The well '{initial_well_source_plate}' does not exist in the labware {self.APINameSamplePlate}, check for typos")
			
		# Check that initial labware and final labware has 8 rows so the multi-channel pipette works
		if len(definition_source_plate["ordering"][0]) != 8 or len(definition_final_plate["ordering"][0]) != 8:
			raise Exception ("Either the sample labware of the final labware does not have 8 rows, which is neccesary for this protocol with 8-channel pipette to work")
		
		# Check that the first well with a sample + number of samples does not exceed the source plate wells
		for index_plate, number_reactions in enumerate(self.samplesPerPlate[:self.numberSourcePlates]):
			if len(definition_source_plate["wells"].keys()) < number_reactions+list(definition_source_plate["wells"].keys()).index(self.firstWellSamplePerPlate[index_plate]):
				raise Exception(f"Having the {self.firstWellSamplePerPlate[index_plate]} as the first well with sample and {number_reactions} wells with sample does not fit in the {self.APINameSamplePlate} labware")
		
		# Finally, we check that the volume of media or sample to transfer is not 0
		if self.volumeAntibiotic <= 0 or self.volumeSample <= 0:
			raise Exception("Neither 'Volume of Sample to Transfer (uL)' or 'Volume of Media to Transfer (uL)' can be lower or equal than 0 ul")
		
class SetParameters:
	"""
	After the checking the UserVariable class we can assign what we will be using to track the plates
	and working with the variables setted in that class
	"""
	def __init__(self, deck_positions):
		self.sumSamples = 0
		self.numberAntibiotics = 0
		self.pipR = None
		self.pipL = None
		self.samplePlates = {}
		self.incubationPlates = {}
		self.antibioticWells = {}
		self.deckPositions = {key: None for key in range(1,deck_positions)}
		self.colors_mediums = ["#ffbb51"] # Initial filled with the one color of the sample
		self.liquid_samples = None # Initial
		self.sameTiprack = None

	def assign_variables(self, user_variables, protocol):
		self.liquid_samples = protocol.define_liquid(
			name = "Sample",
			description = "Sample that will be inoculated with the selected medium",
			display_color = "#ffbb51"
		)
		
		self.numberAntibiotics = len(user_variables.nameAntibiotics)
		
		# Pipette Variables
		self.pipR = protocol.load_instrument(user_variables.APINamePipR, mount = "right")
		self.pipL = protocol.load_instrument(user_variables.APINamePipL, mount = "left")
		
		if self.pipR.channels != 8:
			raise Exception("Right pipette needs to have 8 channels, i.e., multi channel")
		if self.pipL.channels != 1:
			raise Exception("Left pipette needs to have 1 channel, i.e., single channel")
		
		if user_variables.APINameTipR == user_variables.APINameTipL:
			self.sameTiprack = True
		else:
			self.sameTiprack = False

		# Check if the volumes can be picked with these set of pipettes
		if self.pipR.min_volume > user_variables.volumeSample or self.pipL.min_volume > user_variables.volumeAntibiotic:
			raise Exception ("Either the volume 'Volume of Sample to Transfer (uL)' or the volume 'Volume of Media to Transfer (uL)' cannot be picked by the set pipettes, try another set of volumes or pipettes")
			
		if user_variables.valueReplaceTiprack.lower() == "true":
			self.replaceTiprack = True
		elif user_variables.valueReplaceTiprack.lower() == "false":
			self.replaceTiprack = False
		else:
			raise Exception("Replace Tiprack Variable can only have 2 possible values: True or False")
		
		# Antibiotic Tubes
		for antibiotic in user_variables.nameAntibiotics:
			self.antibioticWells[antibiotic] = {"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":0, "Definition Liquid": None}
			
			while True:
				color_liquid = f"#{random.randint(0, 0xFFFFFF):06x}"
				if color_liquid.lower() != "#ffbb51" and color_liquid.lower() not in self.colors_mediums:
					self.antibioticWells[antibiotic]["Definition Liquid"] = protocol.define_liquid(
						name = f"{antibiotic}",
						description = f"Medium {antibiotic}",
						display_color = color_liquid
					)
					self.colors_mediums.append(color_liquid)
					break
			
		# Source Plates
		self.sumSamples = sum(user_variables.samplesPerPlate[:user_variables.numberSourcePlates])
		
		incubation_plates_needed = 0
		for index_plate in range(user_variables.numberSourcePlates):
			self.samplePlates[index_plate] = {"Number Samples":user_variables.samplesPerPlate[index_plate],
											   "Position":None,
											   "Label":f"Source Plate {index_plate+1}",
											   "Antibiotics":user_variables.antibioticsPerPlate[index_plate].replace(" ","").split(","),
											   "Opentrons Place":None,
											   "Index First Well Sample": opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameSamplePlate)["groups"][0]["wells"].index(user_variables.firstWellSamplePerPlate[index_plate]),
											   "First Column Sample": None}
			self.samplePlates[index_plate]["First Column Sample"] = int(self.samplePlates[index_plate]["Index First Well Sample"]/len(opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameSamplePlate)["ordering"][0]))
			
			# Incubation Plates
			for antibiotic_source_plate in self.samplePlates[index_plate]["Antibiotics"]:
				# Initialize with the values that we can set now
				self.incubationPlates[incubation_plates_needed] = {"Source Plate":index_plate,
														   "Position":None,
														   "Label":f"Samples Plate {index_plate+1} with {antibiotic_source_plate}",
														   "Antibiotic":antibiotic_source_plate,
														   "Number Samples":self.samplePlates[index_plate]["Number Samples"],
														   "Opentrons Place":None}
				incubation_plates_needed += 1
			
			# Add to the antibiotic number of reactions how many from this source plate does it need
			for antibiotic_plate in self.samplePlates[index_plate]["Antibiotics"]:
				self.antibioticWells[antibiotic_plate]["Number Total Reactions"] += self.samplePlates[index_plate]["Number Samples"]
		

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

	The pipette needs to have a tip to perform this function

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
		
# Body of the Program
# ----------------------------------
# ----------------------------------
		
metadata = {
'apiLevel':'2.14'
}
# It is API level 2.14 so we can do the load_liquids and not take more 

def run(protocol:opentrons.protocol_api.ProtocolContext):
	labware_context = opentrons.protocol_api.labware
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Read Variables Excel, define the user and protocol variables and check them for initial errors
	
	# Read Excel
	excel_variables = pd.read_excel("/data/user_storage/VariablesPlateIncubation.xlsx", sheet_name = None, engine = "openpyxl")
	# excel_variables = pd.read_excel("VariablesPlateIncubation.xlsx", sheet_name = None, engine = "openpyxl")
	# Let's check that the minimal sheets
	name_sheets = list(excel_variables.keys())

	if not all(item in name_sheets for item in ["GeneralVariables","PerPlateVariables","PipetteVariables"]):
		raise Exception('The Excel file needs to have the sheets "GeneralVariables","PerPlateVariables" and "PipetteVariables"\nThey must have those names')
	
	# Check that all variable sheets have the needed columns and variable names
	general_variables = excel_variables.get("GeneralVariables")
	plate_variables = excel_variables.get("PerPlateVariables")
	pip_variables = excel_variables.get("PipetteVariables")

	if not all(item in list(general_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'GeneralVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in general_variables["Variable Names"].values for item in ['Name Source Plate', 'Number of Source Plates', 'Name Final Plate', 'Volume of Sample to Transfer (uL)', 'Name Medias', 'Volume of Media to Transfer (uL)', 'Name 15mL Tuberack']):
			raise Exception("'GeneralVariables' sheet table needs to have 7 rows with the following names: 'Name Source Plate', 'Number of Source Plates', 'Name Final Plate', 'Volume of Sample to Transfer (uL)', 'Name Medias', 'Volume of Media to Transfer (uL)', 'Name 15mL Tuberack'")
		
	if "Variable Names" not in list(plate_variables.columns):
		raise Exception("'PerPlateVariables' sheet table needs to have at least 1 column, 'Variable Names'")
	else:
		if not all(item in plate_variables["Variable Names"].values for item in ['Samples per plate', 'Media(s) per plate', 'First Well With Sample']):
			raise Exception("'PerPlateVariables' Sheet table needs to have 3 rows with the following names: 'Samples per plate', 'Media(s) per plate', 'First Well With Sample'")
	
	if not all(item in list(pip_variables.columns) for item in ["Value", "Variable Names"]):
		raise Exception("'PipetteVariables' sheet table needs to have only 2 columns: 'Variable Names' and 'Value'")
	else:
		if not all(item in pip_variables["Variable Names"].values for item in ['Name Right Pipette (Multichannel)', 'API Name Right Pipette TipRack', 'Name Left Pipette (Singlechannel)', 'API Name Left Pipette TipRack','Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks']):
			raise Exception("'PipetteVariables' Sheet table needs to have 7 rows with the following names: 'Name Right Pipette (Multichannel)', 'API Name Right Pipette TipRack', 'Name Left Pipette (Singlechannel)', 'API Name Left Pipette TipRack','Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks'")
	
	user_variables = UserVariables(general_variables, plate_variables, pip_variables)
	user_variables.check(protocol)
	program_variables = SetParameters(len(protocol.deck))
	program_variables.assign_variables(user_variables, protocol)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Assign the sample source plates and the final ones that the number is already set
	
	# We start settign the source labware which number has been provided
	labware_source = setting_labware(user_variables.numberSourcePlates, user_variables.APINameSamplePlate, program_variables.deckPositions, protocol, label = "Sample Souce Plate")
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_source}
	
	
	# Now we assign each labware position to ther place in the SetteParameters class
	# Get the max volume of the liquid in each well to fill it after with liquid
	vol_max_well_source_labware = list(labware_context.get_labware_definition(user_variables.APINameSamplePlate)["wells"].values())[0]['totalLiquidVolume']
	for index_labware, labware in enumerate(labware_source.items()):
		program_variables.samplePlates[index_labware]["Position"] = labware[0]
		program_variables.samplePlates[index_labware]["Opentrons Place"] = labware[1]
		
		# Set the liquid of samples
		for well in program_variables.samplePlates[index_labware]["Opentrons Place"].wells()[program_variables.samplePlates[index_labware]["Index First Well Sample"]:(program_variables.samplePlates[index_labware]["Index First Well Sample"]+program_variables.samplePlates[index_labware]["Number Samples"])]:
			well.load_liquid(program_variables.liquid_samples, volume = 0.9*vol_max_well_source_labware)
		
	# Set the final plates which number has been calculates in the assign_variables method of the clas SettedParameters
	# First lets get the labels
	labels_incubation_plates = []
	for final_plate in program_variables.incubationPlates.values():
		labels_incubation_plates.append(final_plate["Label"])

	labware_final = setting_labware(len(program_variables.incubationPlates.keys()), user_variables.APINameIncubationPlate, program_variables.deckPositions, protocol, label = labels_incubation_plates)
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_final}
	# Now we are going to assign to which final plates the samples from the source plates should go
	for index_labware, labware in enumerate(labware_final.items()):
		program_variables.incubationPlates[index_labware]["Position"] = labware[0]
		program_variables.incubationPlates[index_labware]["Opentrons Place"] = labware[1]
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Calculate how many reactives labware do we need and set it in the deck
	
	# First we need to know the max reactive tube volume
	# For that we need to know the maximum volume of the tubes and how many tubes of the reactives we need in total
	first_key = list(labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"].keys())[0]
	max_volume_well = labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"][first_key]["totalLiquidVolume"]
	
	total_falcons_antibiotics = 0 # Initialize
	for antibiotic_type in program_variables.antibioticWells.keys():
		# return (number_tubes, reactions_per_tube, initial_volume_tubes)
		number_tubes, program_variables.antibioticWells[antibiotic_type]["Reactions Per Tube"], program_variables.antibioticWells[antibiotic_type]["Volumes"] = number_tubes_needed(user_variables.volumeAntibiotic, program_variables.antibioticWells[antibiotic_type]["Number Total Reactions"], 0.9*max_volume_well)
		# The 0.9 max well volume is only to not overfill the volume and give space to put more liquid so the pipetting is assure
		total_falcons_antibiotics += number_tubes
	
	# Set how many tuberacks now that we now how many tubes of antibiotic we need
	number_wells_tuberack = len(labware_context.get_labware_definition(user_variables.APINameFalconPlate)["wells"])
	tuberacks_needed = math.ceil(total_falcons_antibiotics/number_wells_tuberack)
	
	labware_falcons = setting_labware(tuberacks_needed, user_variables.APINameFalconPlate, program_variables.deckPositions, protocol, label = "Reactive Labware")
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_falcons}
	
	# Now we are going to set the reactives in the coldblock positions, we need to keep track of these positions for liquid movement
	# Get the possible positions merging all the labwares from the tuberacks
	positions_tuberack = []
	for labware in labware_falcons.values():
		positions_tuberack += labware.wells()
	generator_positions_antibiotics = generator_positions(positions_tuberack)
	
	# Assign to each antibiotic the positions of the falcons
	for antibiotic_type in program_variables.antibioticWells.keys():
		for volume_tube in program_variables.antibioticWells[antibiotic_type]["Volumes"]:
			well_tube_falcon = next(generator_positions_antibiotics)
			program_variables.antibioticWells[antibiotic_type]["Positions"].append(well_tube_falcon)
			well_tube_falcon.load_liquid(liquid = program_variables.antibioticWells[antibiotic_type]["Definition Liquid"], volume = volume_tube)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Distribute the antibiotic to their corresponding plates
	for antibiotic_type in program_variables.antibioticWells.keys():
		check_tip_and_pick(program_variables.pipL, user_variables.APINameTipL, program_variables.deckPositions, protocol, initial_tip = user_variables.startingTipPipL, replace_tiprack = user_variables.replaceTiprack, same_tiprack = program_variables.sameTiprack)
		wells_distribute_antibiotic = []
		for number_plate, plate_incubation in program_variables.incubationPlates.items():
			if plate_incubation["Antibiotic"] == antibiotic_type:
				wells_distribute_antibiotic += plate_incubation["Opentrons Place"].wells()[:plate_incubation["Number Samples"]]
		for index_tube, tube in enumerate(program_variables.antibioticWells[antibiotic_type]["Reactions Per Tube"]):
			if len(wells_distribute_antibiotic) <= tube:
				program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube] = distribute_z_tracking_falcon15ml (program_variables.pipL,
												  program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube],
												  user_variables.volumeAntibiotic,
												  program_variables.antibioticWells[antibiotic_type]["Positions"][index_tube],
												  wells_distribute_antibiotic)
				tube -= len(wells_distribute_antibiotic)
				
			else:
				program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube] = distribute_z_tracking_falcon15ml (program_variables.pipL,
												  program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube],
												  user_variables.volumeAntibiotic,
												  program_variables.antibioticWells[antibiotic_type]["Positions"][index_tube],
												  wells_distribute_antibiotic[:tube])
				del wells_distribute_antibiotic[:tube]
				tube -= len(wells_distribute_antibiotic)
				
		program_variables.pipL.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Transfer colonies to different plates
	for final_plate in program_variables.incubationPlates.values():
		number_column_samples = math.ceil(final_plate["Number Samples"]/program_variables.pipR.channels)
		initial_column = program_variables.samplePlates[final_plate["Source Plate"]]["First Column Sample"]
		for index_column in range(number_column_samples):
			check_tip_and_pick(program_variables.pipR, user_variables.APINameTipR, program_variables.deckPositions, protocol, replace_tiprack = user_variables.replaceTiprack, initial_tip = user_variables.startingTipPipR, same_tiprack = program_variables.sameTiprack)
			program_variables.pipR.transfer(user_variables.volumeSample,
											program_variables.samplePlates[final_plate["Source Plate"]]["Opentrons Place"].columns()[initial_column+index_column],
											final_plate["Opentrons Place"].columns()[index_column],
											new_tip="never")
			program_variables.pipR.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Homing
	protocol.home()
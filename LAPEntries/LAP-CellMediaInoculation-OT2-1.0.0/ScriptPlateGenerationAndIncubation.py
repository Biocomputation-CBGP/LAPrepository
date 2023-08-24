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
		self.numberSourcePlates = general[general["Variables Names"] == "Number of Source Plates"]["Value"].values[0]
		self.samplesPerPlate = list(each_plate[each_plate["Variables Names"] == "Samples per plate"].values[0][1:])
		self.firstWellSamplePerPlate = list(each_plate[each_plate["Variables Names"] == "First Well With Sample"].values[0][1:])
		self.nameAntibiotics = general[general["Variables Names"] == "Name Medias"]["Value"].values[0]

		self.volumeAntibiotic = general[general["Variables Names"] == "Volume of Media to Transfer (uL)"]["Value"].values[0]
		self.volumeSample = general[general["Variables Names"] == "Volume of Sample to Transfer (uL)"]["Value"].values[0]
		self.APINamePipR = pipettes[pipettes["Variables Names"] == "Name Right Pipette (Multichannel)"]["Value"].values[0]
		self.APINamePipL = pipettes[pipettes["Variables Names"] == "Name Left Pipette (Singlechannel)"]["Value"].values[0]
		
		self.startingTipPipR = pipettes[pipettes["Variables Names"] == "Initial Tip Right Pipette"]["Value"].values[0]
		self.startingTipPipL = pipettes[pipettes["Variables Names"] == "Initial Tip Left Pipette"]["Value"].values[0]
		self.APINameSamplePlate = general[general["Variables Names"] == "Name Source Plate"]["Value"].values[0]
		self.APINameIncubationPlate = general[general["Variables Names"] == "Name Final Plate"]["Value"].values[0]
		self.APINameFalconPlate = general[general["Variables Names"] == "Name 15mL Tuberack"]["Value"].values[0]
		self.valueReplaceTiprack = pipettes[pipettes["Variables Names"] == "Replace Tipracks"]["Value"].values[0]
		self.APINameTipR = pipettes[pipettes["Variables Names"] == "API Name Right Pipette TipRack"]["Value"].values[0]
		self.APINameTipL = pipettes[pipettes["Variables Names"] == "API Name Left Pipette TipRack"]["Value"].values[0]
		
		self.antibioticsPerPlate = list(each_plate[each_plate["Variables Names"] == "Media(s) per plate"].values[0][1:])
		
		self.replaceTiprack = pipettes[pipettes["Variables Names"] == "Replace Tipracks"]["Value"].values[0]
		
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
	def __init__(self):
		self.sumSamples = 0
		self.numberAntibiotics = 0
		self.pipR = None
		self.pipL = None
		self.samplePlates = {}
		self.incubationPlates = {}
		self.antibioticWells = {}
		self.deckPositions = {key: None for key in range(1,12)}
		self.colors_mediums = ["#ffbb51"] # Initial filled with the one color of the sample
		self.liquid_samples = None # Initial
		
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
	
	# Check that all variable sheets have the needed columns and variables names
	general_variables = excel_variables.get("GeneralVariables")
	plate_variables = excel_variables.get("PerPlateVariables")
	pip_variables = excel_variables.get("PipetteVariables")

	if not all(item in list(general_variables.columns) for item in ["Value", "Variables Names"]):
		raise Exception("'GeneralVariables' sheet table needs to have only 2 columns: 'Variables Names' and 'Value'")
	else:
		if not all(item in general_variables["Variables Names"].values for item in ['Name Source Plate', 'Number of Source Plates', 'Name Final Plate', 'Volume of Sample to Transfer (uL)', 'Name Medias', 'Volume of Media to Transfer (uL)', 'Name 15mL Tuberack']):
			raise Exception("'GeneralVariables' sheet table needs to have 7 rows with the following names: 'Name Source Plate', 'Number of Source Plates', 'Name Final Plate', 'Volume of Sample to Transfer (uL)', 'Name Medias', 'Volume of Media to Transfer (uL)', 'Name 15mL Tuberack'")
		
	if "Variables Names" not in list(plate_variables.columns):
		raise Exception("'PerPlateVariables' sheet table needs to have at least 1 column, 'Variables Names'")
	else:
		if not all(item in plate_variables["Variables Names"].values for item in ['Samples per plate', 'Media(s) per plate', 'First Well With Sample']):
			raise Exception("'PerPlateVariables' Sheet table needs to have 3 rows with the following names: 'Samples per plate', 'Media(s) per plate', 'First Well With Sample'")
	
	if not all(item in list(pip_variables.columns) for item in ["Value", "Variables Names"]):
		raise Exception("'PipetteVariables' sheet table needs to have only 2 columns: 'Variables Names' and 'Value'")
	else:
		if not all(item in pip_variables["Variables Names"].values for item in ['Name Right Pipette (Multichannel)', 'API Name Right Pipette TipRack', 'Name Left Pipette (Singlechannel)', 'API Name Left Pipette TipRack','Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks']):
			raise Exception("'PipetteVariables' Sheet table needs to have 7 rows with the following names: 'Name Right Pipette (Multichannel)', 'API Name Right Pipette TipRack', 'Name Left Pipette (Singlechannel)', 'API Name Left Pipette TipRack','Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks'")
	
	user_variables = UserVariables(general_variables, plate_variables, pip_variables)
	user_variables.check(protocol)
	program_variables = SetParameters()
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
		check_tip_and_pick(program_variables.pipL, program_variables.deckPositions, user_variables, protocol)
		wells_distribute_antibiotic = []
		for number_plate, plate_incubation in program_variables.incubationPlates.items():
			if plate_incubation["Antibiotic"] == antibiotic_type:
				wells_distribute_antibiotic += plate_incubation["Opentrons Place"].wells()[:plate_incubation["Number Samples"]]
		for index_tube, tube in enumerate(program_variables.antibioticWells[antibiotic_type]["Reactions Per Tube"]):
			if len(wells_distribute_antibiotic) <= tube:
				distribute_z_tracking_falcon15ml (program_variables.pipL,
												  program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube],
												  user_variables.volumeAntibiotic,
												  program_variables.antibioticWells[antibiotic_type]["Positions"][index_tube],
												  wells_distribute_antibiotic)
				tube -= len(wells_distribute_antibiotic)
				program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube] -= len(wells_distribute_antibiotic)*user_variables.volumeAntibiotic
			else:
				distribute_z_tracking_falcon15ml (program_variables.pipL,
												  program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube],
												  user_variables.volumeAntibiotic,
												  program_variables.antibioticWells[antibiotic_type]["Positions"][index_tube],
												  wells_distribute_antibiotic[:tube])
				del wells_distribute_antibiotic[:tube]
				tube -= len(wells_distribute_antibiotic)
				program_variables.antibioticWells[antibiotic_type]["Volumes"][index_tube] -= len(wells_distribute_antibiotic)*user_variables.volumeAntibiotic
		program_variables.pipL.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Transfer colonies to different plates
	for final_plate in program_variables.incubationPlates.values():
		number_column_samples = math.ceil(final_plate["Number Samples"]/program_variables.pipR.channels)
		initial_column = program_variables.samplePlates[final_plate["Source Plate"]]["First Column Sample"]
		for index_column in range(number_column_samples):
			check_tip_and_pick(program_variables.pipR, program_variables.deckPositions, user_variables, protocol)
			program_variables.pipR.transfer(user_variables.volumeSample,
											program_variables.samplePlates[final_plate["Source Plate"]]["Opentrons Place"].columns()[initial_column+index_column],
											final_plate["Opentrons Place"].columns()[index_column],
											new_tip="never")
			program_variables.pipR.transfer(5, program_variables.samplePlates[0]["Opentrons Place"].columns()[0], final_plate["Opentrons Place"].columns()[0], new_tip="never")
			program_variables.pipR.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Homing
	protocol.home()
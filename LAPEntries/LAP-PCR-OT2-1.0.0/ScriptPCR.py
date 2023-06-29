"""
Python script destined to OT-2
This script performs a preparation of PCR mix and, optionally, the CPR temperature profile ina thermocycler
This script needs an excel file attached to perform the running
For more info go to https://github.com/Biocomputation-CBGP/LAPrepository/tree/main/LAPEntries,
https://github.com/Biocomputation-CBGP/OT2/tree/main/PCRsamplePreparationand/or
https://www.protocols.io/view/ot-2-pcr-sample-preparation-protocol-n92ldpyznl5b/v1
"""

## Packages needed for the running of the protocol
import opentrons
import pandas as pd
import random
import math
import numpy as np
from opentrons.motion_planning.deck_conflict import DeckConflictError #in version 2.14


class UserVariables:
	def __init__(self, general, each_plate, pipettes, reagents, modules, profile = None):
		"""
		This function will take the pandas dataframe that will be the table of the excel variable files
		"""
		self.numberSourcePlates = general[general["Variable Name"] == "Number of Source Plates"]["Value"].values[0]
		self.samplesPerPlate = list(each_plate[each_plate["Variable Name"] == "Number Samples"].values[0][1:])
		self.firstWellSamplePerPlate = list(each_plate[each_plate["Variable Name"] == "Well Start"].values[0][1:])
		self.volumesSamplesPerPlate = reagents[reagents["Variable Name"] == "Volume sample DNA Template (uL)"]["Value"].values[0]
		self.finalMapName = general[general["Variable Name"] == "Final Map Name"]["Value"].values[0]
		self.wellStartFinalPlate = general[general["Variable Name"] == "Well Start Final PCR Plate"]["Value"].values[0]
		
		self.sets = reagents[reagents["Variable Name"] == "Number sets"]["Value"].values[0]
		self.numberPrimerSet = reagents[reagents["Variable Name"] == "Number primer/set"]["Value"].values[0]
		self.polymerase = reagents[reagents["Variable Name"] == "Volume polymerase mix (uL)"]["Value"].values[0]
		self.primer = reagents[reagents["Variable Name"] == "Volume each primer (uL)"]["Value"].values[0]
		self.finalVolume = reagents[reagents["Variable Name"] == "Final volume (uL)"]["Value"].values[0]
		self.extraPipettingFactor = reagents[reagents["Variable Name"] == "Extra Pipetting Factor"]["Value"].values[0]
		
		self.APINamePipL = pipettes[pipettes["Variable Name"] == "API Name Left Pipette"]["Value"].values[0]
		self.APINamePipR = pipettes[pipettes["Variable Name"] == "API Name Right Pipette"]["Value"].values[0]
		self.startingTipPipR = pipettes[pipettes["Variable Name"] == "Initial Tip Right Pipette"]["Value"].values[0]
		self.startingTipPipL = pipettes[pipettes["Variable Name"] == "Initial Tip Left Pipette"]["Value"].values[0]
		self.APINameSamplePlate = general[general["Variable Name"] == "API Name Source Plate"]["Value"].values[0]
		self.APINameFinalPlate = general[general["Variable Name"] == "API Name Final PCR Plate"]["Value"].values[0]
		self.APINameEppendorfPlate = general[general["Variable Name"] == "API Name Eppendorf Reagents Rack"]["Value"].values[0]
		self.APINameTipR = pipettes[pipettes["Variable Name"] == "API Name Tiprack Right Pipette"]["Value"].values[0]
		self.APINameTipL = pipettes[pipettes["Variable Name"] == "API Name Tiprack Left Pipette"]["Value"].values[0]
		self.replaceTiprack = pipettes[pipettes["Variable Name"] == "Replace Tipracks"]["Value"].values[0]
		
		self.positionsControls = list(each_plate[each_plate["Variable Name"] == "Position Controls"].values[0][1:])
		self.positionsNotPCR = list(each_plate[each_plate["Variable Name"] == "Wells not to perform PCR"].values[0][1:])
		
		self.presenceHS = modules[modules["Variables Names"] == "Presence Thermocycler"]["Value"].values[0]
		self.presenceTermo = modules[modules["Variables Names"] == "Presence Heater-Shaker"]["Value"].values[0]
		self.finalStateLid = modules[modules["Variables Names"] == "Final Open Lid"]["Value"].values[0]
		self.temperatureLid = modules[modules["Variables Names"] == "Temperature Lid"]["Value"].values[0]
		self.finalTemperatureBlock = modules[modules["Variables Names"] == "Hold Block Temperature"]["Value"].values[0]
		self.rpm = modules[modules["Variables Names"] == "RPM Heater-Shaker"]["Value"].values[0]
		self.APINameLabwareHS = modules[modules["Variables Names"] == "API Name Heater-Shaker Labware"]["Value"].values[0]
		self.pause = modules[modules["Variables Names"] == "Pause Before Temperature Program"]["Value"].values[0]

		self.temperatureProfile = profile.dropna(how="all")
		
	def check(self, protocol):
		"""
		Function that will check the variables of the Template and will raise errors that will crash the OT run
		It is a validation function of the variables checking errors or inconsistencies

		This function is dependant again with the variabels that we have, some checks are interchangable between protocols, but some of them are specific of the variables
		"""

		# Check all the boolean values ans setting them
		if str(self.presenceHS).lower() == "true":
			self.presenceHS = True
		elif str(self.presenceHS).lower() == "false":
			self.presenceHS = False
		else:
			raise Excpetion ("The variable 'Presence Heater-Shaker' only accepts 2 values, True or False")
		
		if str(self.replaceTiprack).lower() == "true":
			self.replaceTiprack = True
		elif str(self.replaceTiprack).lower() == "false":
			self.replaceTiprack = False
		else:
			raise Excpetion ("The variable 'Replace Tipracks' only accepts 2 values, True or False")
		
		if str(self.presenceTermo).lower() == "true":
			self.presenceTermo = True
		elif str(self.presenceTermo).lower() == "false":
			self.presenceTermo = False
		else:
			raise Excpetion ("The variable 'Presence Thermocycler' only accepts 2 values, True or False")
		
		if self.presenceTermo:
			if str(self.finalStateLid).lower() == "true":
				self.finalStateLid = True
			elif str(self.finalStateLid).lower() == "false":
				self.finalStateLid = False
			else:
				raise Excpetion ("The variable 'Final Open Lid' only accepts 2 values, True or False meaning at the end of the themnorcycler steps the lid will be open or close, respectivelly")
		
			if str(self.pause).lower() == "true":
				self.pause = True
			elif str(self.pause).lower() == "false":
				self.pause = False
			else:
				raise Excpetion ("The variable 'Pause Before Temperature Program' only accepts 2 values, True or False")
				
		else:
			self.finalStateLid = None
			self.pause = None
		
		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if any(pd.isna(elem) == True for elem in self.samplesPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.samplesPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Number Samples' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.firstWellSamplePerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.firstWellSamplePerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Well Start' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == False for elem in self.positionsControls[self.numberSourcePlates:]):
			raise Exception("The values of 'Position Controls' need to be in the column of the plate is going to be used and they have to be in consecutive columns")
		if any(pd.isna(elem) == False for elem in self.positionsNotPCR[self.numberSourcePlates:]):
			raise Exception("The values of 'Wells not to perform PCR' need to be in the column of the plate is going to be used and they have to be in consecutive columns")
		
		try:
			definition_source_plate = labware_context.get_labware_definition(self.APINameSamplePlate)
			definition_final_plate = labware_context.get_labware_definition(self.APINameFinalPlate)
			definition_rack = labware_context.get_labware_definition(self.APINameEppendorfPlate)
			if pd.isna(self.APINamePipR) == False:
				definition_tiprack_right = labware_context.get_labware_definition(self.APINameTipR)
			if pd.isna(self.APINamePipL) == False:
				definition_tiprack_left = labware_context.get_labware_definition(self.APINameTipL)
			if self.presenceHS:
				definition_rack_HS = labware_context.get_labware_definition(self.APINameLabwareHS)
		except:
			raise Exception("One or more of the introduced labwares or tipracks are not in the labware directory of the opentrons. Check for any typo of the api labware name.")
		
		# Check if there is any typo in the starting tip of both pipettes
		if pd.isna(self.APINamePipR) == False and (self.startingTipPipR not in definition_tiprack_right["groups"][0]["wells"]):
			raise Exception("Starting tip of right pipette is not valid, check for typos")
		if pd.isna(self.APINamePipL) == False and (self.startingTipPipL not in definition_tiprack_left["groups"][0]["wells"]):
			raise Exception("Starting tip of left pipette is not valid, check for typos")
		
		# Check if the well of the starting plate exist in the final labware
		for initial_well_source_plate in self.firstWellSamplePerPlate[:self.numberSourcePlates]:
			if initial_well_source_plate not in list(definition_source_plate["wells"].keys()):
				raise Exception(f"The well '{initial_well_source_plate}' does not exist in the labware {self.APINameSamplePlate}, check for typos")
		
		# Check if final start well exists in the finla labware
		if initial_well_final_plate not in list(definition_source_plate["wells"].keys()):
			raise Exception(f"The well '{initial_well_final_plate}' does not exist in the labware {self.APINameFinalPlate}, check for typos")
		
		# We are going to check that the number of cells in each plate is not larger than the capacity of the source plates
		for number_plate, number_cells_per_plate in enumerate(self.samplesPerPlate):
			if type(number_cells_per_plate) != int and number_plate < self.numberSourcePlates:
				raise Exception("Every cell of Samples per plate has to be a number or an empty cell")
			if len(definition_source_plate["wells"]) < number_cells_per_plate:
				raise Exception("Number of cells is larger than the capacity of the source plate labware")
		
		# Volume of reactives is larger than the established one
		if (self.primer*self.numberPrimerSet + self.polymerase + self.self.volumesSamplesPerPlate) > self.finalVolume:
			raise Exception("Volume of each reactive added plus the volume of DNA template is larger than the total volume of reactives")
		
		return
	
class SettedParameters:
	def __init__(self):
		self.sumSamples = 0
		self.pipR = None
		self.pipL = None
		self.sameTiprack = None
		self.samplePlates = {}
		self.finalPlates = {}
		self.reactiveWells = {}
		self.setsWells = {}
		self.deckPositions = {key: None for key in range(1,12)}
		self.volPolymeraseFactor = 0
		self.volPrimerFactor = 0
		self.volTotal = 0
		self.volTotalFactor = 0
		self.volWaterFactor = 0
		self.volWater = 0
		self.tc_mod = None
		self.colors_mediums = ["#ffbb51", "#10D21B", "#A7AEF9"] # Initial filled with the one color of the sample
		self.liquid_samples = None # Initial
		
		return
	
	def assign_variables(self, user_variables, protocol):
		self.liquid_samples = protocol.define_liquid(
			name = "Sample",
			description = "Sample that will be inoculated with the selected medium",
			display_color = "#ffbb51"
		)
		
		self.volTotal = user_variables.finalVolume-user_variables.volumesSamplesPerPlate
		self.volTotalFactor = self.volTotal*(1+user_variables.extraPipettingFactor)
		
		self.volPolymeraseFactor = user_variables.polymerase*(1+user_variables.extraPipettingFactor)
		self.volPrimerFactor = user_variables.primer*(1+user_variables.extraPipettingFactor)
		
		self.volWater = self.volTotal-user_variables.polymerase-(user_variables.primer*user_variables.numberPrimerSet)
		self.volWaterFactor = self.volWater*(1+user_variables.extraPipettingFactor)
		
		self.hs_mods = {} # It woill be filled during the run of the protocol
		
		# Pipette Variables
		if pd.isna(user_variables.APINamePipL) == False:
			self.pipL = protocol.load_instrument(user_variables.APINamePipL, mount = "left")
		if pd.isna(user_variables.APINamePipR) == False:
			self.pipR = protocol.load_instrument(user_variables.APINamePipR, mount = "right")
			
		if user_variables.presenceTermo:
			self.tc_mod = protocol.load_module("thermocycler")
			self.tc_mod.open_lid()
			self.deckPositions = {**self.deckPositions, **{7:"Thermocycler",8:"Thermocycler",10:"Thermocycler",11:"Thermocycler"}}
		
		# Source Plates Definition
		for index_plate in range(user_variables.numberSourcePlates):
			if pd.isna(user_variables.positionsControls[index_plate]):
				control_positions = []
			else:
				control_positions = user_variables.positionsControls[index_plate].replace(" ","").split(",")
			
			if pd.isna(user_variables.positionsNotPCR[index_plate]):
				positions_notPCR = []
			else:
				positions_notPCR = user_variables.positionsNotPCR[index_plate].replace(" ","").split(",")
			self.samplePlates[index_plate] = {"Number Samples":user_variables.samplesPerPlate[index_plate],
											  "Position":None,
											  "Label":f"Source Plate {index_plate+1}",
											  "Opentrons Place":None,
											  "Index First Well Sample": opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameSamplePlate)["groups"][0]["wells"].index(user_variables.firstWellSamplePerPlate[index_plate]),
											  "Control Positions": control_positions,
											  "Positions Not Perform PCR": positions_notPCR}
			self.sumSamples += self.samplePlates[index_plate]["Number Samples"] - len(self.samplePlates[index_plate]["Positions Not Perform PCR"]) # In this we already take in account the controls because they are inside of the number samples
		
		# Final Plate Variables
		# Lets find first how many final plates do we need
		number_wells_final_plate = len(opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["wells"])
		number_source_needed = math.ceil((opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)+self.sumSamples*user_variables.sets)/number_wells_final_plate)
		for index_plate in range(number_source_needed):
			self.finalPlates[index_plate] = {"Source Plate":index_plate,
											"Position":None,
											"Label":f"Selected Samples Plate {index_plate+1}",
											"Opentrons Place":None,
											"Map Samples with Sets":None # We will create this map when we establish the final plate
											}
			
		# Create the reactives dictionary
		# First we define the know reactives
		self.reactiveWells =  {
			"Polymerase":{"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples*user_variables.sets
						  ,"Definition Liquid": protocol.define_liquid(name = "Polymerase Mix", description = "Polymerase mix with polymerase, buffer and nucleotides", display_color = "#10D21B")
						  },
			"Water":{"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples*user_variables.sets
					 ,"Definition Liquid": protocol.define_liquid(name = "Water", description = "Sterile Water", display_color = "#A7AEF9")
					 }
			}
		
		# Now we add the needed primers
		for index_primer in range(int(user_variables.sets*user_variables.numberPrimerSet)):
			self.reactiveWells[f"Primer {index_primer+1}"] = {"Positions":[], "Volumes":None, "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples
															  ,"Definition Liquid":None
															  }
			primer_number = index_primer+1
			while True:
				color_liquid = f"#{random.randint(0, 0xFFFFFF):06x}"
				if color_liquid.lower() not in self.colors_mediums:
					
					self.reactiveWells[f"Primer {primer_number}"]["Definition Liquid"] = protocol.define_liquid(
						name = f"Primer {primer_number}",
						description = f"Reagent Primer {primer_number}",
						display_color = color_liquid
					)
					self.colors_mediums.append(color_liquid)
					
					break
			
			
		# Now we add the sets
		for index_set in range(int(user_variables.sets)):
			self.setsWells[f"Set {index_set+1}"] = {"Positions":[], "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples, "Set Primers":[], "HS":None}
			for primer in range(int(index_set*user_variables.numberPrimerSet), int((index_set*user_variables.numberPrimerSet)+user_variables.numberPrimerSet)):
				self.setsWells[f"Set {index_set+1}"]["Set Primers"].append(f"Primer {primer+1}")
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

def run_program_PCR(tc_mod, program, lid_temperature, final_lid_state, final_block_state, volume_sample, protocol):
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

def z_positions_mix(vol_mixing):
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

def mixing_eppendorf_15(eppendorf_mixing, volume_tube, program_variables, user_variables, protocol):
	"""
	This is a function to perfrom an extensive mixing of every eppendorf which should be done before distributing the reactives along the final plates
	
	Mixing is one of the most crucial parts of this workflow and that is why theer is a function only for it
	
	This function will perform the mixing and will return warnings (in case that is needed) and the final pipette that has been used
	"""
	# This function is going to perform the mixing of the tubes in the coldblock (it is setted for the 1500ul eppendorf because the positions are done manually)
	mastermix_mixing_volume_theory = vvolume_tube / 3
	try:
		aSuitablePippet_mixing = give_me_optimal_pipette_to_use(mastermix_mixing_volume_theory, variables.right_pipette, variables.left_pipette)
		max_vol_pipette = aSuitablePippet_mixing.max_volume
		if max_vol_pipette < mastermix_mixing_volume_theory:
			volume_mixing = max_vol_pipette
		else:
			volume_mixing = mastermix_mixing_volume_theory
			pass
	except: # If this happens it means that the the volume is too low to any of the pipettes
		if program_variables.pipR.min_volume < program_variables.pipL.min_volume:
			volume_mixing = program_variables.pipR.min_volume
			aSuitablePippet_mixing = program_variables.pipR
		else:
			volume_mixing = program_variables.pipL.min_volume
			aSuitablePippet_mixing = program_variables.pipL
		
	if aSuitablePippet_mixing.has_tip():
		pass
	else:
		if aSuitablePippet_mixing.mount == "right" and program_variables.pipL.has_tip:
			program_variables.pipL.drop_tip()
		elif aSuitablePippet_mixing.mount == "left" and program_variables.pipR.has_tip:
			program_variables.pipR.drop_tip()
		check_tip_and_pick (aSuitablePippet_mixing, program_variables.deckPositions, user_variables, protocol)
	
	# After calculating the mixing volume, choosing a pipette and picking up a tip we perform the mix
	positions_mixing = z_positions_mix(volume_mixing) # This is the part that is customized for the 1500uL eppendorfs
	
	# We are going to mix 7 times at different heighs of the tube
	aSuitablePippet_mixing.mix(7, volume_mixing, location_mixing.bottom(z=positions_mixing[1])) 
	aSuitablePippet_mixing.mix(7, volume_mixing, location_mixing.bottom(z=positions_mixing[0])) 
	aSuitablePippet_mixing.mix(7, volume_mixing, location_mixing.bottom(z=positions_mixing[2])) 
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -20, radius=0.7, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -20, radius=0.5, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -27, radius=0.3, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -27, radius=0.3, speed=30)
	aSuitablePippet_mixing.touch_tip(location_mixing,v_offset = -27, radius=0.3, speed=30)
	# Now we are going to aspirate and dispense 3 times at different heights to mix a little bit more the content of the tube
	for i in range(2):
		aSuitablePippet_mixing.aspirate(volume_mixing, location_mixing.bottom(z=positions_mixing[0]))
		aSuitablePippet_mixing.dispense(volume_mixing, location_mixing.bottom(z=positions_mixing[2]))
	for i in range(2):
		aSuitablePippet_mixing.aspirate(volume_mixing, location_mixing.bottom(z=positions_mixing[2]))
		aSuitablePippet_mixing.dispense(volume_mixing, location_mixing.bottom(z=positions_mixing[0]))
	aSuitablePippet_mixing.blow_out(location_mixing.center())
	
	return aSuitablePippet_mixing

def tube_to_tube_transfer (vol_transfer_reaction, positions_source_tubes, reactions_source_tubes, positions_final_tubes, reactions_final_tubes, program_variables, user_variables, protocol):
	index_source_tube = 0 # Initial
	pipette_use = program_variables.pipL #Initial
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
			pipette_use.transfer(volume_transfer, positions_source_tubes[index_source_tube], final_tube, new_tip = "never")

			# Define the source tube
			if reactions_source_tubes[index_source_tube] == 0:
				index_source_tube += 1
	
	pipette_use.drop_tip()
	
	return

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
	try:
		excel_variables = pd.read_excel("/data/user_storage/VariablesPCR.xlsx", sheet_name = ["GeneralVariables","SamplesPlateVariables","PipetteVariables","ModuleVariables","ReagentsPerReaction","TemperatureProfile"], engine = "openpyxl")
		user_variables = UserVariables(excel_variables.get("GeneralVariables"), excel_variables.get("SamplesPlateVariables"), excel_variables.get("PipetteVariables"),excel_variables.get("ReagentsPerReaction"),excel_variables.get("ModuleVariables"),excel_variables.get("TemperatureProfile"))
	except:
		excel_variables = pd.read_excel("/data/user_storage/VariablesPCR.xlsx", sheet_name = ["GeneralVariables","SamplesPlateVariables","PipetteVariables","ModuleVariables","ReagentsPerReaction"], engine = "openpyxl")
		user_variables = UserVariables(excel_variables.get("GeneralVariables"), excel_variables.get("SamplesPlateVariables"), excel_variables.get("PipetteVariables"),excel_variables.get("ReagentsPerReaction"),excel_variables.get("ModuleVariables"))
	user_variables.check(protocol)
	program_variables = SettedParameters()
	program_variables.assign_variables(user_variables, protocol)
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Setting the HS needed because they have more restrictions in the OT-2 and cannot be done with the setting labware function because setting the HS in a position will not give errors but after it wont work
	# First let's find how many tubes we need of mixes in case we have the HS
	if user_variables.presenceHS:
		first_key = list(labware_context.get_labware_definition(user_variables.APINameLabwareHS)["wells"].keys())[0]
		vol_max_tube = labware_context.get_labware_definition(user_variables.APINameLabwareHS)["wells"][first_key]["totalLiquidVolume"]
		number_wells_labware = len(labware_context.get_labware_definition(user_variables.APINameLabwareHS)["wells"])
		number_tubes_mix_hs, reactions_per_tube_mix_hs, volumes_tubes_mix_hs = number_tubes_needed (program_variables.volTotalFactor, program_variables.sumSamples, vol_max_tube*0.9)
		
		for index_set in range(int(user_variables.sets)):
			program_variables.setsWells[f"Set {index_set+1}"]["Reactions Per Tube"] = reactions_per_tube_mix_hs
			program_variables.setsWells[f"Set {index_set+1}"]["Volumes"] = volumes_tubes_mix_hs
		
		possible_positions = [1,3,4,6,7,10]
		number_hs = math.ceil(number_tubes_mix_hs*user_variables.numberPrimerSet/number_wells_labware)
		
		for position in possible_positions:
			try:
				labware_hs = protocol.load_module('heaterShakerModuleV1',position)
				labware_hs.close_labware_latch()
				labware_hs.load_labware(user_variables.APINameLabwareHS, label = f"Eppendorf Rack with Mix on Slot {position}")
				program_variables.deckPositions[position] = "Heater Shaker"
				program_variables.hs_mods[position] = labware_hs
				number_hs -= 1
			except DeckConflictError:
				continue
			except:
				raise Exception ("Not possible to establish the Heater Shaker, try another combination of variables")
			
			if number_hs == 0:
				break
		
		
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Setting the Labware that we already now how many of them we have
	
	# Source Plates
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
	
	# Final Plate
	# Set the final plates which number has been calculates in the assign_variables method of the clas SettedParameters
	
	if user_variables.presenceTermo:
		program_variables.tc_mod.load_labware(user_variables.APINameSamplePlate)
		labware_final = {7: program_variables.tc_mod.labware}
	else:
		labware_final = setting_labware(user_variables.numberSourcePlates, user_variables.APINameFinalPlate, program_variables.deckPositions, protocol, label = "Sample Souce Plate")
		program_variables.deckPositions = {**program_variables.deckPositions , **labware_source}
	
	# Now we are going to assign to which final plates the samples from the source plates should go
	for index_labware, labware in enumerate(labware_final.items()):
		program_variables.finalPlates[index_labware]["Position"] = labware[0]
		program_variables.finalPlates[index_labware]["Opentrons Place"] = labware[1]
		program_variables.finalPlates[index_labware]["Map Samples with Sets"] = MapLabware(labware[1])
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Setting the coldblocks that we need for the reactives
	# Let's find how many tubes we need for all the reactives
	first_key = list(labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"].keys())[0]
	vol_max_tube = labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"][first_key]["totalLiquidVolume"]
	
	total_number_tubes = 0
	
	number_tubes_water, program_variables.reactiveWells["Water"]["Reactions Per Tube"], program_variables.reactiveWells["Water"]["Volumes"] = number_tubes_needed (program_variables.volWaterFactor, program_variables.sumSamples*int(user_variables.sets), vol_max_tube*0.9)
	total_number_tubes += number_tubes_water
	number_tubes_poly, program_variables.reactiveWells["Polymerase"]["Reactions Per Tube"], program_variables.reactiveWells["Polymerase"]["Volumes"]  = number_tubes_needed (program_variables.volPolymeraseFactor, program_variables.sumSamples*int(user_variables.sets), vol_max_tube*0.9)
	total_number_tubes += number_tubes_poly
	number_tubes_primer, reactions_per_tube_primer, volumes_tubes_primer = number_tubes_needed (program_variables.volPrimerFactor, program_variables.sumSamples, vol_max_tube*0.9)
	total_number_tubes += number_tubes_primer*user_variables.numberPrimerSet*user_variables.sets
	for index_primer in range(int(user_variables.sets*user_variables.numberPrimerSet)):
		program_variables.reactiveWells[f"Primer {index_primer+1}"]["Reactions Per Tube"] = reactions_per_tube_primer
		program_variables.reactiveWells[f"Primer {index_primer+1}"]["Volumes"] = volumes_tubes_primer
		
	if user_variables.presenceHS == False:
		number_tubes_mix, reactions_per_tube_mix, volumes_tubes_mix = number_tubes_needed (program_variables.volTotalFactor, program_variables.sumSamples, vol_max_tube*0.9)
		total_number_tubes += number_tubes_mix*user_variables.sets
		for index_set in range(user_variables.sets):
			program_variables.setsWells[f"Set {index_set+1}"]["Reactions Per Tube"] = reactions_per_tube_mix
			program_variables.setsWells[f"Set {index_set+1}"]["Volumes"] = volumes_tubes_mix
	
	# Set the number of tubes in the coldblock
	number_coldblocks = math.ceil(total_number_tubes/len(labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"]))
	coldblocks = setting_labware(number_coldblocks, user_variables.APINameEppendorfPlate, program_variables.deckPositions, protocol, label = "Reagents")
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
			well_tube_eppendorf = next(generator_positions_reagents)
			program_variables.reactiveWells[reagent_type]["Positions"].append(well_tube_eppendorf)
			well_tube_eppendorf.load_liquid(liquid = program_variables.reactiveWells[reagent_type]["Definition Liquid"], volume = math.ceil(volume_tube))
	
	# Now we state the mix tubes, which can go in the HS or the Coldblock
	if user_variables.presenceHS == False:
		for index_set in range(user_variables.sets):
			program_variables.setsWells[f"Set {index_set+1}"]["HS"] = False
			for volume_tube in program_variables.setsWells[f"Set {index_set+1}"]["Volumes"]:
				well_tube_eppendorf = next(generator_positions_reagents)
				program_variables.reactiveWells[reagent_type]["Positions"].append(well_tube_eppendorf)
	
	elif user_variables.presenceHS == True:
		wells_hs = []
		for hs in list(program_variables.hs_mods.values()):
			wells_hs += hs.labware.wells()
		generator_wells_hs = generator_positions(wells_hs)
		for index_set in range(int(user_variables.sets)):
			program_variables.setsWells[f"Set {index_set+1}"]["HS"] = False
			for volume_tube in program_variables.setsWells[f"Set {index_set+1}"]["Volumes"]:
				well_tube_eppendorf = next(generator_wells_hs)
				program_variables.setsWells[f"Set {index_set+1}"]["Positions"].append(well_tube_eppendorf)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Create the mixes
	tubes_sets = []
	reactions_tubes = []
	for set_primers in program_variables.setsWells.values():
		tubes_sets += set_primers["Positions"]
		reactions_tubes += set_primers["Reactions Per Tube"]
	# Transfer Water
	tube_to_tube_transfer(program_variables.volWaterFactor, program_variables.reactiveWells["Water"]["Positions"], program_variables.reactiveWells["Water"]["Reactions Per Tube"], tubes_sets, reactions_tubes[:], program_variables, user_variables, protocol)
	# Transfer Polymerase
	# Lower the aspiration and dispense rate
	if program_variables.pipR != None:
		default_values_pipR = [program_variables.pipR.flow_rate.aspirate, program_variables.pipR.flow_rate.dispense]
		program_variables.pipR.flow_rate.aspirate = program_variables.pipR.min_volume
		program_variables.pipR.flow_rate.dispense= program_variables.pipR.min_volume
	if program_variables.pipL != None:
		default_values_pipL = [program_variables.pipL.flow_rate.aspirate, program_variables.pipL.flow_rate.dispense]
		program_variables.pipL.flow_rate.aspirate = program_variables.pipL.min_volume
		program_variables.pipL.flow_rate.dispense= program_variables.pipL.min_volume
	
	tube_to_tube_transfer(program_variables.volPolymeraseFactor, program_variables.reactiveWells["Polymerase"]["Positions"], program_variables.reactiveWells["Polymerase"]["Reactions Per Tube"], tubes_sets, reactions_tubes[:], program_variables, user_variables, protocol)
	
	if program_variables.pipR != None:
		program_variables.pipR.flow_rate.aspirate = default_values_pipR[0]
		program_variables.pipR.flow_rate.dispense= default_values_pipR[1]
	if program_variables.pipL != None:
		program_variables.pipL.flow_rate.aspirate = default_values_pipL[0]
		program_variables.pipL.flow_rate.dispense=default_values_pipL[1]
	# Transfer Primers
	for set_primers in program_variables.setsWells.values():
		for primer in set_primers["Set Primers"]:
			tube_to_tube_transfer(program_variables.volPrimerFactor, program_variables.reactiveWells[primer]["Positions"], program_variables.reactiveWells[primer]["Reactions Per Tube"][:], set_primers["Positions"], set_primers["Reactions Per Tube"][:], program_variables, user_variables, protocol)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Mix and Distribute Sets
	index_start_final_plate = opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)
	wells_distribute = []
	for final_labware in program_variables.finalPlates.values():
		wells_distribute += final_labware["Opentrons Place"].wells()
	wells_distribute_free = wells_distribute[index_start_final_plate:int(index_start_final_plate+user_variables.sets*program_variables.sumSamples)]
	for name, set_primer in program_variables.setsWells.items():
		# Mix the set of primers first
		optimal_pipette = optimal_pipette_use(program_variables.volTotal, program_variables.pipR, program_variables.pipL)
		for index, tube in enumerate(set_primer["Positions"]):
			if user_variables.presenceHS == True:
				# Find out in which HS is the tube and shake it
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].set_and_wait_for_shake_speed(user_variables.rpm)
				protocol.delay(seconds=10)
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].deactivate_shaker()
				if optimal_pipette.has_tip == False:
					check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
				optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_free[:set_primer["Reactions Per Tube"][index]], new_tip="never",disposal_volume=0)
			else:
				# Mix it with a pipette
				last_pipette = mixing_eppendorf_15(tube, volumes_tubes_mixing, program_variables, variables_define_tiprack, protocol)
				if optimal_pipette == last_pipette:
					optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_free[:set_primer["Reactions Per Tube"][index]], new_tip="never",disposal_volume=0)
				else:
					check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
					optimal_pipette.distribute(program_variables.volTotal, tube, wells_distribute_free[:set_primer["Reactions Per Tube"][index]], new_tip="never",disposal_volume=0)
					
			del wells_distribute_free[:set_primer["Reactions Per Tube"][index]]
		optimal_pipette.drop_tip()
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Transfer Samples to final wells
	optimal_pipette = optimal_pipette_use(user_variables.volumesSamplesPerPlate, program_variables.pipR, program_variables.pipL)
	# Take the wells that we are not going to pick up and move the controls to the end
	all_samples_transfer = []
	for source_plate in program_variables.samplePlates.values():
		wells = source_plate["Opentrons Place"].wells()[source_plate["Index First Well Sample"]:source_plate["Index First Well Sample"]+source_plate["Number Samples"]]
		for notPCR in source_plate["Positions Not Perform PCR"]:
			try:
				wells.remove(source_plate["Opentrons Place"][notPCR])
			except:
				next
		for control in source_plate["Control Positions"]:
			try:
				wells.remove(source_plate["Opentrons Place"][control])
			except:
				pass
			wells.append(source_plate["Opentrons Place"][control])
		all_samples_transfer += wells
	# Create the generator of wells to distribute
	final_wells = generator_positions(wells_distribute)
	for number_set in range(int(user_variables.sets)):
		for well_source in all_samples_transfer:
			well_pcr = next(final_wells)
			check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
			optimal_pipette.transfer(user_variables.volumesSamplesPerPlate, well_source, well_pcr, new_tip="never")
			optimal_pipette.drop_tip()
			
			# Map it
			for finalplate in program_variables.finalPlates.values():
				if str(finalplate["Position"]) == str(well_pcr).split(" ")[-1]:
					finalplate["Map Samples with Sets"].assign_value(f"{well_source} with Set {number_set+1}", well_pcr._core._row_name, well_pcr._core._column_name)
	# Export map(s)
	for final_plate in program_variables.finalPlates.values():
		final_plate["Map Samples with Sets"].export_map(f'{user_variables.finalMapName}.csv')
		
	# Perform PCR profile
	if user_variables.presenceTermo:
		if user_variables.pause:
			protocol.pause("Protocol is pause so plate in thermocyler can be mix or user can put caps on it")
		
		program_variables.tc_mod.close_lid()
		run_program_PCR(program_variables.tc_mod, user_variables.temperatureProfile, user_variables.temperatureLid, user_variables.finalStateLid, user_variables.finalTemperatureBlock, user_variables.finalVolume, protocol)
	
	# Final home
	protocol.home()
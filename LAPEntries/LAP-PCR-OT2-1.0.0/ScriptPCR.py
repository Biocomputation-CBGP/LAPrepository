"""
Python script destined to OT-2
This script performs a preparation of PCR mix and, optionally, the CPR temperature profile in a thermocycler
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
from opentrons.motion_planning.deck_conflict import DeckConflictError #in version 6.3.1
from opentrons.protocol_api.labware import OutOfTipsError # in version 6.3.1


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
		self.mapID = list(each_plate[each_plate["Variable Name"] == "Map IDs"].values[0][1:])
		
		self.presenceHS = modules[modules["Variable Name"] == "Presence Heater-Shaker"]["Value"].values[0]
		self.presenceTermo = modules[modules["Variable Name"] == "Presence Thermocycler"]["Value"].values[0]
		self.finalStateLid = modules[modules["Variable Name"] == "Final Open Lid"]["Value"].values[0]
		self.temperatureLid = modules[modules["Variable Name"] == "Temperature Lid"]["Value"].values[0]
		self.finalTemperatureBlock = modules[modules["Variable Name"] == "Hold Block Temperature"]["Value"].values[0]
		self.rpm = modules[modules["Variable Name"] == "RPM Heater-Shaker"]["Value"].values[0]
		self.APINameLabwareHS = modules[modules["Variable Name"] == "API Name Heater-Shaker Labware"]["Value"].values[0]
		self.pause = modules[modules["Variable Name"] == "Pause Before Temperature Program"]["Value"].values[0]

		# Temperature profile, in case it needs it
		if isinstance(profile, pd.DataFrame):
			self.temperatureProfile = profile.dropna(how="all")
		else:
			self.temperatureProfile = None
		
	def check(self, protocol):
		"""
		Function that will check the variables of the Template and will raise errors that will crash the OT run
		It is a validation function of the variables checking errors or inconsistencies

		This function is dependant again with the variabels that we have, some checks are interchangable between protocols, but some of them are specific of the variables
		"""
		labware_context = opentrons.protocol_api.labware
		
		# Check that the needed variables are in the Sheets
		if pd.isna([self.numberSourcePlates, self.finalMapName, self.wellStartFinalPlate, self.APINameSamplePlate, self.APINameFinalPlate, self.APINameEppendorfPlate]).any():
			raise Exception("No variable in the sheet 'GeneralVariables' can be left empty")
		
		if pd.isna([self.sets, self.numberPrimerSet, self.polymerase, self.primer, self.finalVolume, self.extraPipettingFactor, self.volumesSamplesPerPlate]).any():
			raise Exception("No variable in the sheet 'ReagentsPerReaction' can be left empty")
		
		# Check all the boolean values ans setting them
		if str(self.presenceHS).lower() == "true":
			self.presenceHS = True
		elif str(self.presenceHS).lower() == "false":
			self.presenceHS = False
		else:
			raise Exception ("The variable 'Presence Heater-Shaker' only accepts 2 values, True or False")
		
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
			if str(self.finalStateLid).lower() == "true":
				self.finalStateLid = True
			elif str(self.finalStateLid).lower() == "false" or pd.isna(self.finalStateLid):
				self.finalStateLid = False
			else:
				raise Exception ("The variable 'Final Open Lid' only accepts 3 values, True, False or left empty, meaning that at the end of the thermocycler steps the lid will be open, in the first case, or close, in the case of the last two values")
		
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
					
			if pd.isna(self.temperatureLid):
				raise Exception ("If the thermocycler is present, the variable 'Temperature Lid' needs to have a value")
			
			if self.temperatureLid > 110 or self.temperatureLid < 37:
				raise Exception("Lid temperature cannot be set with the thermocycler, the operative range of the thermocycler is 37-110C")
			
		else:
			self.finalStateLid = None
			self.pause = None
			self.temperatureLid = None
			
		if self.presenceHS:
			if pd.isna(self.rpm) or pd.isna(self.APINameLabwareHS):
				raise Exception ("If the Heater-Shaker is present there are 2 variables that cannot be left empty: 'RPM Heater-Shaker' and 'API Name Heater-Shaker Labware'")
		else:
			self.rpm = None
			self.APINameLabwareHS = None
		
		# Check that tehre is at least 1 pipette
		if pd.isna(self.APINamePipL) and pd.isna(self.APINamePipR):
			raise Exception("There must be at least 1 pipette set to perform this protocol")
		
		# Check if there is some value of the plates where it shouldnt in the per plate sheet
		if any(pd.isna(elem) == True for elem in self.samplesPerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.samplesPerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Number Samples' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == True for elem in self.firstWellSamplePerPlate[:self.numberSourcePlates]) or any(pd.isna(elem) == False for elem in self.firstWellSamplePerPlate[self.numberSourcePlates:]):
			raise Exception("The values of 'Well Start' need to be as many as the 'Number of Source Plates' and be in consecutive columns")
		if any(pd.isna(elem) == False for elem in self.positionsControls[self.numberSourcePlates:]):
			raise Exception("The values of 'Position Controls' need to be in the column of the plate is going to be used and they have to be in consecutive columns")
		if any(pd.isna(elem) == False for elem in self.positionsNotPCR[self.numberSourcePlates:]):
			raise Exception("The values of 'Wells not to perform PCR' need to be in the column of the plate is going to be used and they have to be in consecutive columns")
		if any(pd.isna(elem) == False for elem in self.mapID[self.numberSourcePlates:]):
			raise Exception("The values of 'Map IDs' need to be in the column of the plate is going to be used and they have to be in consecutive columns")
		
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
		except OSError: # This would be catching the FileNotFoundError that happens when a labware is not found
			raise Exception("One or more of the introduced labwares or tipracks are not in the labware directory of the opentrons. Check for any typo of the api labware name.")
		
		# Check if there is any typo in the starting tip of both pipettes
		if pd.isna(self.APINamePipR) == False and (self.startingTipPipR not in definition_tiprack_right["groups"][0]["wells"]):
			raise Exception("Starting tip of right pipette is not valid, check for typos")
		if pd.isna(self.APINamePipL) == False and (self.startingTipPipL not in definition_tiprack_left["groups"][0]["wells"]):
			raise Exception("Starting tip of left pipette is not valid, check for typos")
		
		# Check if the well of the starting plate exist in the final labware
		for index_plate, initial_well_source_plate in enumerate(self.firstWellSamplePerPlate[:self.numberSourcePlates]):
			if initial_well_source_plate not in list(definition_source_plate["wells"].keys()):
				raise Exception(f"The well '{initial_well_source_plate}' does not exist in the labware {self.APINameSamplePlate}, check for typos")
			# Check if the number of samples plus the start well can fit in the initial labware
			if list(definition_source_plate["wells"].keys()).index(initial_well_source_plate) + self.samplesPerPlate[index_plate] > len(definition_source_plate["wells"]):
				raise Exception(f"The Plate {index_plate + 1} has {self.samplesPerPlate[index_plate]} samples starting from the well {initial_well_source_plate}. That does not fit in the labware {self.APINameSamplePlate}")
		
		# Check if final start well exists in the final labware
		if self.wellStartFinalPlate not in list(definition_source_plate["wells"].keys()):
			raise Exception(f"The well '{self.wellStartFinalPlate}' does not exist in the labware {self.APINameSamplePlate}, check for typos")
		
		# Check that the establish controls are in the source labware
		for index_plate, pos_controls in enumerate(self.positionsControls[:self.numberSourcePlates]):
			if not pd.isna(pos_controls):
				controls = pos_controls.replace(" ","").split(",")
				for pos_control in controls:
					if pos_control not in list(definition_source_plate["wells"].keys()):
						raise Exception(f"The control position {pos_control} of Plate {index_plate + 1} not in the labware {self.APINameSamplePlate}. Check for typos")
					
		# Check the positions not to take are in the source labware
		for index_plate, pos_notPCR in enumerate(self.positionsNotPCR[:self.numberSourcePlates]):
			if not pd.isna(pos_notPCR):
				not_pcr = pos_notPCR.replace(" ","").split(",")
				for pos_notPCR in not_pcr:
					if pos_notPCR not in list(definition_source_plate["wells"].keys()):
						raise Exception(f"The well {pos_notPCR} of Plate {index_plate + 1} not in the labware {self.APINameSamplePlate}. Check for typos")
					
		# We are going to check that the number of cells in each plate is not larger than the capacity of the source plates
		for number_plate, number_cells_per_plate in enumerate(self.samplesPerPlate):
			if type(number_cells_per_plate) != int and number_plate < self.numberSourcePlates:
				raise Exception("Every cell of Samples per plate has to be a number or an empty cell")
			if len(definition_source_plate["wells"]) < number_cells_per_plate:
				raise Exception("Number of cells is larger than the capacity of the source plate labware")
		
		# Volume of reactives is larger than the established one
		if (self.primer*self.numberPrimerSet + self.polymerase + self.volumesSamplesPerPlate) > self.finalVolume:
			raise Exception("Volume of each reactive added plus the volume of DNA template is larger than the total volume of reactives")	
		
		# Check if the extra pipetting factor is between 0 an d1
		if pd.isna(self.extraPipettingFactor):
			self.extraPipettingFactor = 0
		else:
			if self.extraPipettingFactor > 1 or self.extraPipettingFactor < 0:
				raise Exception("The variable 'Extra Pipetting Factor' from the sheet 'ReagentsPerReaction' should be a number between 0 and 1")
		
		# Check the rest of the variables in the sheet ReagentsPerReaction are not 0:
		if any(element <= 0 for element in [self.sets, self.numberPrimerSet, self.polymerase, self.primer, self.finalVolume, self.volumesSamplesPerPlate]):
			raise Exception("Only the value of 'Extra Pipetting Factor' in the sheet ReagentsPerReaction can be 0")
		
		# Check that the Number of samples plate is not 0
		if self.numberSourcePlates == 0:
			raise Exception("We need to have at least 1 plate with the DNA templates to create the PCR final plates")
		
		# Check that the Samples per plate sheet it is not empty
		if not self.samplesPerPlate or not self.mapID or not self.firstWellSamplePerPlate:
			raise Exception("The sheet SamplesPlateVariables cannot be left completely empty")
		
		# Check the maps provided exist
		for map_name in self.mapID[:self.numberSourcePlates]:
			if pd.isna(map_name):
				pass
			else:
				try:
					# map_dataframe = pd.read_excel("VariablesPCR.xlsx", sheet_name = map_name, index_col = 0, engine = "openpyxl")
					map_dataframe = pd.read_excel("/data/user_storage/VariablesPCR.xlsx", sheet_name = map_name, index_col = 0, engine = "openpyxl")
				except ValueError: # Error that appears when the sheet 'map_name' does not exist in the excel file
					raise Exception(f"The map of IDs '{map_name}' does not exist in the Excel file")
				
				# Check that the provided maps are accord to the set labware
				map_rows, map_columns = map_dataframe.shape
				if map_rows != len(definition_source_plate["ordering"][0]) or map_columns != len(definition_source_plate["ordering"]):
					raise Exception(f"The Sheet '{map_name}' needs to have the same columns and rows as the labware '{self.APINameSamplePlate}'")
		
		return
	
class SettedParameters:
	def __init__(self):
		self.sumSamples = 0
		self.pipR = None
		self.pipL = None
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
		self.colors_mediums = ["#ffbb51", "#10D21B", "#3d85c6", "#d3cfcf", "#ff5151", "#783f04"] # Initial filled with the one color of the sample: sample, polymerase, water, mix, not pick samples, controls
		self.liquid_samples = None # Initial
		self.liquid_control = None # Initial
		self.liquid_notpick = None # Initial
		
		return
	
	def assign_variables(self, user_variables, protocol):
		self.liquid_samples = protocol.define_liquid(
			name = "Sample",
			description = "Sample that will be inoculated with the selected medium",
			display_color = "#ffbb51"
		)
		
		self.liquid_notpick = protocol.define_liquid(
			name = "Sample Not Pick",
			description = "Sample that will not be taken to perform a PCR",
			display_color = "#ff5151"
		)                                                                                                      
		
		self.liquid_control = protocol.define_liquid(
			name = "Control",
			description = "Sample that will act as control and will be placed at the end of each set",
			display_color = "#783f04"
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
		else:
			# Establish all the variables set to the left pipette as none
			user_variables.APINameTipL = None
			user_variables.startingTipPipL = None
			
		if pd.isna(user_variables.APINamePipR) == False:
			self.pipR = protocol.load_instrument(user_variables.APINamePipR, mount = "right")
		else:
			# Establish all the variables set to the left pipette as none
			user_variables.APINameTipR = None
			user_variables.startingTipPipR = None
			
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
											  "Positions Not Perform PCR": positions_notPCR,
											  "Map Names":None}
			self.sumSamples += self.samplePlates[index_plate]["Number Samples"] - len(self.samplePlates[index_plate]["Positions Not Perform PCR"]) # In this we already take in account the controls because they are inside of the number samples
			
		# Final Plate Variables
		# Lets find first how many final plates do we need
		number_wells_final_plate = len(opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["wells"])
		number_source_needed = math.ceil((opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)+self.sumSamples*user_variables.sets)/number_wells_final_plate)
		if user_variables.presenceTermo and number_source_needed > 1:
			raise Exception("If 'Presence Thermocycler' is True we can only have 1 final plate and for this protocol to run there is a need for more final plates, try less samples or lest set of primers")
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
					 ,"Definition Liquid": protocol.define_liquid(name = "Water", description = "Sterile Water", display_color = "#3d85c6")
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
			self.setsWells[f"Set {index_set+1}"] = {"Positions":[], "Reactions Per Tube":None, "Number Total Reactions":self.sumSamples, "Set Primers":[]
													,"Definition Liquid":protocol.define_liquid(
														name = f"Set {index_set+1}",
														description = f"Eppendorf with Set {index_set+1}. Leave empty!",
														display_color = "#d3cfcf")
													}
			
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
	excel_variables = pd.read_excel("/data/user_storage/VariablesPCR.xlsx", sheet_name = None, engine = "openpyxl")
	# excel_variables = pd.read_excel("VariablesPCR.xlsx", sheet_name = None, engine = "openpyxl")
	# Let's check that the minimal sheets
	name_sheets = list(excel_variables.keys())
	
	if not all(item in name_sheets for item in ["GeneralVariables","ReagentsPerReaction","PipetteVariables","SamplesPlateVariables","ModuleVariables"]):
		raise Exception('The Excel file needs to have min the sheets "GeneralVariables","ReagentsPerReaction","PipetteVariables","SamplesPlateVariables" and "ModuleVariables"\nThey must have those names')
	
	# Check that all variable sheets have the needed columns and variables names
	general_variables = excel_variables.get("GeneralVariables")
	reagents_variables = excel_variables.get("ReagentsPerReaction")
	plate_variables = excel_variables.get("SamplesPlateVariables")
	pip_variables = excel_variables.get("PipetteVariables")
	module_variables = excel_variables.get("ModuleVariables")

	if not all(item in list(general_variables.columns) for item in ["Value", "Variable Name"]):
		raise Exception("'GeneralVariables' sheet table needs to have only 2 columns: 'Variable Name' and 'Value'")
	else:
		if not all(item in general_variables["Variable Name"].values for item in ['API Name Source Plate','Number of Source Plates','API Name Final PCR Plate','Well Start Final PCR Plate','API Name Eppendorf Reagents Rack','Final Map Name']):
			raise Exception("'GeneralVariables' sheet table needs to have 6 rows with the following names: 'API Name Source Plate','Number of Source Plates', 'API Name Final PCR Plate', 'Well Start Final PCR Plate','API Name Eppendorf Reagents Rack','Final Map Name'")
		
	if "Variable Name" not in list(plate_variables.columns):
		raise Exception("'SamplesPlateVariables' sheet table needs to have at least 1 column, 'Variable Name'")
	else:
		if not all(item in plate_variables["Variable Name"].values for item in ['Number Samples','Well Start','Position Controls', 'Wells not to perform PCR']):
			raise Exception("'SamplesPlateVariables' Sheet table needs to have 4 rows with the following names: 'Number Samples','Well Start','Position Controls', 'Wells not to perform PCR'")
		if plate_variables.shape[1] < 2:
			raise Exception("'SamplesPlateVariables' Sheet table needs to have at least 2 columns, 1 with the variables names and at least another 1 with the information of the source plate (s)")
	
	if not all(item in list(pip_variables.columns) for item in ["Value", "Variable Name"]):
		raise Exception("'PipetteVariables' sheet table needs to have only 2 columns: 'Variable Name' and 'Value'")
	else:
		if not all(item in pip_variables["Variable Name"].values for item in ['API Name Right Pipette','API Name Left Pipette','API Name Tiprack Left Pipette','API Name Tiprack Right Pipette', 'Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks']):
			raise Exception("'PipetteVariables' Sheet table needs to have 7 rows with the following names: 'API Name Right Pipette','API Name Left Pipette','API Name Tiprack Left Pipette','API Name Tiprack Right Pipette', 'Initial Tip Left Pipette', 'Initial Tip Right Pipette', 'Replace Tipracks'")

	if not all(item in list(reagents_variables.columns) for item in ["Value", "Variable Name"]):
		raise Exception("'ReagentsPerReaction' sheet table needs to have only 2 columns: 'Variable Name' and 'Value'")
	else:
		if not all(item in reagents_variables["Variable Name"].values for item in ['Number primer/set','Number sets','Volume each primer (uL)','Volume polymerase mix (uL)', 'Volume sample DNA Template (uL)', 'Final volume (uL)', 'Extra Pipetting Factor']):
			raise Exception("'ReagentsPerReaction' Sheet table needs to have 7 rows with the following names: 'Number primer/set','Number sets','Volume each primer (uL)','Volume polymerase mix (uL)', 'Volume sample DNA Template (uL)', 'Final volume (uL)', 'Extra Pipetting Factor'")
	
	if not all(item in list(module_variables.columns) for item in ["Value", "Variable Name"]):
		raise Exception("'ModuleVariables' sheet table needs to have only 2 columns: 'Variable Name' and 'Value'")
	else:
		if not all(item in module_variables["Variable Name"].values for item in ['Presence Thermocycler','Presence Heater-Shaker','Final Open Lid','Temperature Lid', 'Hold Block Temperature', 'RPM Heater-Shaker', 'API Name Heater-Shaker Labware','Pause Before Temperature Program']):
			raise Exception("'ModuleVariables' Sheet table needs to have 8 rows with the following names: 'Presence Thermocycler','Presence Heater-Shaker','Final Open Lid','Temperature Lid', 'Hold Block Temperature', 'RPM Heater-Shaker', 'API Name Heater-Shaker Labware','Pause Before Temperature Program'")
	

	if "TemperatureProfile" in name_sheets:
		temperature_variables = excel_variables.get("TemperatureProfile")
		user_variables = UserVariables(general_variables, plate_variables, pip_variables, reagents_variables, module_variables, temperature_variables)
	else:
		user_variables = UserVariables(general_variables, plate_variables, pip_variables, reagents_variables, module_variables)
	
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
				labware_hs.load_labware(user_variables.APINameLabwareHS, label = f"Eppendorf Rack with Mix Slot {position}")
				program_variables.deckPositions[position] = "Heater Shaker"
				program_variables.hs_mods[position] = labware_hs
				number_hs -= 1
			except DeckConflictError:
				continue
			
			if number_hs == 0:
				break
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Setting the Labware that we already now how many of them we have
	
	# Source Plates
	# We start settign the source labware which number has been provided
	
	labware_source = setting_labware(user_variables.numberSourcePlates, user_variables.APINameSamplePlate, program_variables.deckPositions, protocol, label = "Sample Source Plate")
	program_variables.deckPositions = {**program_variables.deckPositions , **labware_source}
	
	# Now we assign each labware position to ther place in the SetteParameters class
	# Get the max volume of the liquid in each well to fill it after with liquid
	vol_max_well_source_labware = list(labware_context.get_labware_definition(user_variables.APINameSamplePlate)["wells"].values())[0]['totalLiquidVolume']
	for index_labware, labware in enumerate(labware_source.items()):
		program_variables.samplePlates[index_labware]["Position"] = labware[0]
		program_variables.samplePlates[index_labware]["Opentrons Place"] = labware[1]
		
		# Establish the maps of the source plate
		if not pd.isna(user_variables.mapID[index_labware]):
			# program_variables.samplePlates[index_labware]["Map Names"] = pd.read_excel("VariablesPCR.xlsx", sheet_name = user_variables.mapID[index_labware], engine = "openpyxl", index_col = 0)
			program_variables.samplePlates[index_labware]["Map Names"] = pd.read_excel("/data/user_storage/VariablesPCR.xlsx", sheet_name = user_variables.mapID[index_labware], engine = "openpyxl", index_col = 0)
			program_variables.samplePlates[index_labware]["Map Names"].columns = program_variables.samplePlates[index_labware]["Map Names"].columns.map(str)
		else:
			program_variables.samplePlates[index_labware]["Map Names"] = pd.DataFrame(np.nan, index = list(labware[1].rows_by_name().keys()), columns = list(labware[1].columns_by_name().keys()))
		
		# Let's check that the labware and map have the same names of the rows and columns
		row_names = list(labware[1].rows_by_name().keys())
		columns_names = list(labware[1].columns_by_name().keys())
		
		rows_map = list(program_variables.samplePlates[index_labware]['Map Names'].index.values)
		columns_map = list(map(str, list(program_variables.samplePlates[index_labware]['Map Names'].columns.values)))
		
		if row_names != rows_map or columns_names != columns_map:
			raise Exception(f"""
The columns and rows of the Maps of DNA Parts {user_variables.mapID[index_labware]} need to have the same names as the ones in {user_variables.APINameSamplePlate}:
		Labware Names:
		 - Column names: {columns_names}
		 - Row names: {row_names}
		Your names:
		 - Sheet Columns: {columns_map}
		 - Sheet Rows: {rows_map}""")
		
		# Set the liquid of samples
		for well in program_variables.samplePlates[index_labware]["Opentrons Place"].wells():
			if well._core._name in program_variables.samplePlates[index_labware]["Control Positions"]:
				well.load_liquid(program_variables.liquid_control, volume = 0.9*vol_max_well_source_labware)
			elif well._core._name in program_variables.samplePlates[index_labware]["Positions Not Perform PCR"]:
				well.load_liquid(program_variables.liquid_notpick, volume = 0.9*vol_max_well_source_labware)
			elif well in program_variables.samplePlates[index_labware]["Opentrons Place"].wells()[program_variables.samplePlates[index_labware]["Index First Well Sample"]:(program_variables.samplePlates[index_labware]["Index First Well Sample"]+program_variables.samplePlates[index_labware]["Number Samples"])]:
				well.load_liquid(program_variables.liquid_samples, volume = 0.9*vol_max_well_source_labware)
		
	# Final Plate
	# Set the final plates which number has been calculates in the assign_variables method of the clas SettedParameters
	
	if user_variables.presenceTermo:
		program_variables.tc_mod.load_labware(user_variables.APINameSamplePlate, label = f"Final PCR Plate Slot 7")
		labware_final = {7: program_variables.tc_mod.labware}
	else:
		labware_final = setting_labware(len(program_variables.finalPlates), user_variables.APINameFinalPlate, program_variables.deckPositions, protocol, label = "Final Plate")
		program_variables.deckPositions = {**program_variables.deckPositions , **labware_final}
	
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
	protocol.comment(str(number_tubes_water))
	protocol.comment(str(program_variables.reactiveWells["Water"]["Reactions Per Tube"]))
	protocol.comment(str(program_variables.reactiveWells["Water"]["Volumes"]))
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
		for index_set in range(int(user_variables.sets)):
			program_variables.setsWells[f"Set {index_set+1}"]["Reactions Per Tube"] = reactions_per_tube_mix
			program_variables.setsWells[f"Set {index_set+1}"]["Volumes"] = volumes_tubes_mix
	
	# Set the number of tubes in the coldblock
	number_coldblocks = math.ceil(total_number_tubes/len(labware_context.get_labware_definition(user_variables.APINameEppendorfPlate)["wells"]))
	coldblocks = setting_labware(number_coldblocks, user_variables.APINameEppendorfPlate, dict(sorted(program_variables.deckPositions.items(),reverse=True)), protocol, label = "Reagents") # To avoid deck conflic errors
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
			if volume_tube == 0:
				continue
			
			well_tube_eppendorf = next(generator_positions_reagents)
			program_variables.reactiveWells[reagent_type]["Positions"].append(well_tube_eppendorf)
			well_tube_eppendorf.load_liquid(liquid = program_variables.reactiveWells[reagent_type]["Definition Liquid"], volume = math.ceil(volume_tube))

	# Now we state the mix tubes, which can go in the HS or the Coldblock
	if user_variables.presenceHS == False:
		for index_set in range(int(user_variables.sets)):
			for volume_tube in program_variables.setsWells[f"Set {index_set+1}"]["Volumes"]:
				well_tube_eppendorf = next(generator_positions_reagents)
				program_variables.setsWells[f"Set {index_set+1}"]["Positions"].append(well_tube_eppendorf)
				well_tube_eppendorf.load_liquid(liquid = program_variables.setsWells[f"Set {index_set+1}"]["Definition Liquid"], volume = 0)
				
	elif user_variables.presenceHS == True:
		wells_hs = []
		for hs in list(program_variables.hs_mods.values()):
			wells_hs += hs.labware.wells()
		generator_wells_hs = generator_positions(wells_hs)
		for index_set in range(int(user_variables.sets)):
			for volume_tube in program_variables.setsWells[f"Set {index_set+1}"]["Volumes"]:
				well_tube_eppendorf = next(generator_wells_hs)
				program_variables.setsWells[f"Set {index_set+1}"]["Positions"].append(well_tube_eppendorf)
				well_tube_eppendorf.load_liquid(liquid = program_variables.setsWells[f"Set {index_set+1}"]["Definition Liquid"], volume = 0)
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Create the mixes
	tubes_sets = []
	reactions_tubes = []
	for set_primers in program_variables.setsWells.values():
		tubes_sets += set_primers["Positions"]
		reactions_tubes += set_primers["Reactions Per Tube"]
	# Transfer Water
	if program_variables.volWaterFactor > 0:
		tube_to_tube_transfer(program_variables.volWaterFactor, program_variables.reactiveWells["Water"]["Positions"], program_variables.reactiveWells["Water"]["Reactions Per Tube"], tubes_sets, reactions_tubes[:], program_variables, user_variables, protocol)

	# Transfer Primers
	for set_primers in program_variables.setsWells.values():
		for primer in set_primers["Set Primers"]:
			tube_to_tube_transfer(program_variables.volPrimerFactor, program_variables.reactiveWells[primer]["Positions"], program_variables.reactiveWells[primer]["Reactions Per Tube"][:], set_primers["Positions"], set_primers["Reactions Per Tube"][:], program_variables, user_variables, protocol)

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
	
	#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	# Mix and Distribute Sets
	index_start_final_plate = opentrons.protocol_api.labware.get_labware_definition(user_variables.APINameFinalPlate)["groups"][0]["wells"].index(user_variables.wellStartFinalPlate)
	wells_distribute = []
	for final_labware in program_variables.finalPlates.values():
		wells_distribute += final_labware["Opentrons Place"].wells()
	wells_distribute_free = wells_distribute[index_start_final_plate:int(index_start_final_plate+user_variables.sets*program_variables.sumSamples)]

	for name, set_primer in program_variables.setsWells.items():
		# Mix the set of primers first
		# Set the optimal pipette to distribute the volume to every well
		optimal_pipette = optimal_pipette_use(program_variables.volTotal, program_variables.pipR, program_variables.pipL)
		for index, tube in enumerate(set_primer["Positions"]):
			if user_variables.presenceHS == True:
				# Find out in which HS is the tube and shake it
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].set_and_wait_for_shake_speed(user_variables.rpm)
				protocol.delay(seconds = 15)
				program_variables.hs_mods[int(str(tube).split(" ")[-1])].deactivate_shaker()
				if optimal_pipette.has_tip == False:
					check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
				optimal_pipette.distribute(float(program_variables.volTotal), tube, wells_distribute_free[:set_primer["Reactions Per Tube"][index]], new_tip="never",disposal_volume=0)
			else:
				# Mix it with a pipette
				last_pipette = mixing_eppendorf_15(tube, set_primer["Volumes"][index], program_variables, user_variables, protocol)
				if optimal_pipette == last_pipette:
					optimal_pipette.distribute(float(program_variables.volTotal), tube, wells_distribute_free[:set_primer["Reactions Per Tube"][index]], new_tip="never",disposal_volume=0)
				else:
					last_pipette.drop_tip()
					check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
					optimal_pipette.distribute(float(program_variables.volTotal), tube, wells_distribute_free[:set_primer["Reactions Per Tube"][index]], new_tip="never",disposal_volume=0)
					
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
			except KeyError: # The value of the list source_plate["Positions Not Perform PCR"] is not in the list wells but exists in the labware (we checked that before in the script)
				next
		for control in source_plate["Control Positions"]:
			try:
				wells.remove(source_plate["Opentrons Place"][control])
			except KeyError: # The value of the list source_plate["Control Positions"] is not in the list wells but exists in the labware (we checked that before in the script)
				pass
			wells.append(source_plate["Opentrons Place"][control])
		all_samples_transfer += wells
	# Create the generator of wells to distribute
	final_wells = generator_positions(wells_distribute)
	for number_set in range(int(user_variables.sets)):
		for well_source in all_samples_transfer:
			well_pcr = next(final_wells)
			check_tip_and_pick (optimal_pipette, program_variables.deckPositions, user_variables, protocol)
			optimal_pipette.transfer(float(user_variables.volumesSamplesPerPlate), well_source, well_pcr, new_tip="never")
			optimal_pipette.drop_tip()
			
			# Map it	
			for sampleplate in program_variables.samplePlates.values():
				if str(sampleplate["Position"]) == str(well_source).split(" ")[-1]:
					# Get value of the well source plate
					value_map_source_well = sampleplate["Map Names"][well_source._core._column_name][well_source._core._row_name]
					if pd.isna(value_map_source_well):
						value_map = f"{well_source._core._row_name}{well_source._core._column_name} Slot {str(well_source).split(' ')[-1]} with Set {number_set+1}"
					else:
						value_map = f"{value_map_source_well} Slot {str(well_source).split(' ')[-1]} with Set {number_set+1}"
					
					# Assign it to the place of the final well in its dataframe
					for finalplate in program_variables.finalPlates.values():
						if str(finalplate["Position"]) == str(well_pcr).split(" ")[-1]:
							finalplate["Map Samples with Sets"].assign_value(value_map, well_pcr._core._row_name, well_pcr._core._column_name)
	
	
	# Export map(s) in an excel
	writer = pd.ExcelWriter(f'/data/user_storage/{user_variables.finalMapName}.xlsx', engine='openpyxl')
	# writer = pd.ExcelWriter(f'{user_variables.finalMapName}.xlsx', engine='openpyxl')
	
	for final_plate in program_variables.finalPlates.values():
		final_plate["Map Samples with Sets"].map.to_excel(writer, sheet_name = f"FinalMapSlot{final_plate['Position']}")
	
	writer.save()
	
	# Perform PCR profile
	if user_variables.presenceTermo:
		if user_variables.pause:
			protocol.pause("Protocol is pause so plate in thermocyler can be mix or user can put caps on it")
		
		program_variables.tc_mod.close_lid()
		run_program_thermocycler(program_variables.tc_mod, user_variables.temperatureProfile, user_variables.temperatureLid, user_variables.finalStateLid, user_variables.finalTemperatureBlock, user_variables.finalVolume, protocol)
	
	# Final home
	protocol.home()
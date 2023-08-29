# Functions Legend
This repository contains the functions used in the LAP entries of the LAP repository.

Each file is one function used in at least 1 LAP entry.


## `check_tip_and_pick`

### Objective

A function that will pick up a tip with the given pipette object.
    	
If there is no tip in the tiprack(s) associated with the pipette, a new tip rack will be defined with the function `define_tiprack`, and the dictionary position\_deck will be updated.

### Tested systems

Opentrons OT-2
	
### Requirements
	
* Error OutOfTipsError from the package opentrons
* `define_tiprack` function
	
### Input
4 Inputs required:
1. **pipette\_used** (_opentrons.protocol_api.instrument_context.InstrumentContext_):

   For example:
        
        P20 Single-Channel GEN2 on right mount object
2. **position\_deck** (_dictionary_): Dictionary with deck positions as keys and labware/module object as the value.

   For example:

       {1: Opentrons 96 Tip Rack 20 µL on 1, 2: Opentrons 96 Tip Rack 20 µL on 2, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None, 11: None}
3. **variables\_define\_tiprack** (_custom class_): script class with attributes APINameTipR (name of the tiprack associated with the right mount pipette) and APINameTipL (name of the tiprack associated with the left mount pipette). 

   For example:

       class Example():
            def __init__ (self):
                self.APINameTipR = opentrons_96_tiprack_20ul
                self.APINameTipL = opentrons_96_tiprack_300ul
4. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)
	 
### Output
* The dictionary _position_deck_ will be updated to have the new tiprack.
* The provided pipette will pick up a tip if a tip rack has been set.
	
### Summary of functioning
1. Pick a tip with the _pipette\_used_ category. If that raises an OutTipError, steps 2 and 3 will be performed. If not, it will exit the function
2. Check if the _pipette\_used_ has any tiprack associated:
	
    __No tip racks associated__
	
    1. A space, if it is available, is designated to the new tiprack with  the function `define_tiprack`

    2. Check with mount the pipette is and assign the starting tip of that pipette

	__Tip rack associated__

	1. Check if the user wants the tip racks to be replaced
	
    	*No replacement tiprack*
    	
    	  1. A tiprack is defined if there is a place, and the dictionary _position_deck_ is updated to reflect that definition
    
    	*Replace tiprack*
    		
    	1. Pause the run so the user can replace the empty tip rack
    	
    	2. Reset tip rack

3. Pick a tip with the _pipette_used_

## `define_tiprack`

### Objective

A function that will define a tiprack associated with a pipette in an available position that does not raise a space conflict error

This function is used in the function `check_tip_and_pick`

### Tested systems

Opentrons OT-2

### Requirements
* Error DeckConflictError from the package opentrons

### Input
4 Inputs required:
1. **pipette** (_opentrons.protocol_api.instrument_context.InstrumentContext_):
       
   For example:
        
       P20 Single-Channel GEN2 on right mount object
2. **position_deck** (_dictionary_): Dictionary with deck positions as keys and labware/module object as the value.
   
   For example:

       {1: Opentrons 96 Tip Rack 20 µL on 1, 2: Opentrons 96 Tip Rack 20 µL on 2, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None, 11: None}
3. **variables_define_tiprack** (_custom class_): script class with attributes APINameTipR (name of the tiprack associated with right mount pipette) and APINameTipL (name of the tiprack associated with left mount pipette).

    For example:
    
       class Example():
            def __init__ (self):
                self.APINameTipR = opentrons_96_tiprack_20ul
                self.APINameTipL = opentrons_96_tiprack_300ul
5. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)

### Output

* Dictionary with the selected position as a key and the tiprack defined as a value.

    For example:

      {3: opentrons_96_tiprack_300ul}

### Summary of functioning

1. Define all positions in the deck that are empty
2. Define which tiprack is the one associated with the given _pipette_ variable
3. Check that the deck has any position left. If not, an Exception is raised
4. Loop over the positions until the tiprack is defined

   1. Try to establish the tiprack. If a _DeckConflictError_ is raised, the loop will go to the free position. If not, the rest of the steps are going to be performed
   2. Check if the tipracks of the left and right pipettes are the same ones

      **Same tiprack**
      1. Define the same tip rack for both pipettes
      
      **Different tipracks**
      1. Define the tip rack on the given pipette
5. If the tiprack has not been defined after the loop, an Exception will be raised

## `distribute_z_tracking_falcon15ml`

### Objective
A function that will distribute from 1 well (15mL falcon tube) to a list of wells tracking the height of the 15mL falcon tube to avoid the pipette getting wet

This function does not track if there is enough volume to transfer to all the wells.

### Tested systems

Opentrons OT-2

### Requirements

* Function `position_dispense_aspirate_falcon15ml`

### Input
5 Inputs required:
1. **pipette_used** (_opentrons.protocol_api.instrument_context.InstrumentContext_): Pipette that will distribute or transfer the _vol_distribute_well_ to the _pos_final_.

   For example:
        
        P20 Single-Channel GEN2 on right mount object
2. **vol_source** (_float_): Initial volume of the _pos_source_. For example:

       10000
3. **vol_distribute_well** (_float_): Volume distributed to the _pos_final_.

   For example:

       15
4. **pos_source** (_opentrons.protocol_api.labware.Well_): Falcon containing the liquid will be distributed to the _pos_final_ wells.

   For example:

       A1 of Opentrons 15 Tube Rack with Falcon 15 mL Conical on 1
5. **pos_final** (_list_): list of positions that the _pipette_used_ will distribute the volume set in _vol_distribute_well_.

   For example:

       [A1 of Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2, A2 of Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2, A3 of Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2]

### Output
* Wells established in _pos_final_ with _vol_distribute_well_ uL volume in them

### Summary of functioning
1. While loop that will go until there are no wells in the list _pos_final_:
    1. Check if the position before and after taking the volume is the same with the function `position_dispense_aspirate_falcon15ml` for the rest of the wells in the _pos_final_
    
        **Same height**
    
        1. _pipette_used_ will distribute the _vol_distribute_well_ to the positions in _pos_final_
        2. Subtract the volume that has been distributed from the _pos_source_
    
        **Different height**
    
        1. Loop over the different length positions in _pos_final_
        2. Check if, with that length position, the position before and after the distribution will be the same
        
            _Same height_
            
            1. Go to the next length position
            
            _Different height_
            
            1. _pipette_used_ will distribute the _vol_distribute_well_ to the positions in _pos_final_
            2. Subtract the volume that has been distributed from the _pos_source_
            3. Break the for-loop

## `find_well_by_value`

### Objective

Given a table or a set of tables, a set value will be searched in them. In case that value is in the given tables, the value of the well
of the labware where that value will be returned.

Otherwise, an exception will be raised if it is not in the table(s) or is repeated within the table.

### Tested systems

Opentrons OT-2

### Requirements


### Input
2 inputs are required:

1. **value** (_string_): Value that will be searched in the given tables.

   For example:
		
	   J23106-RBS_STD-LacI-rpoC-g2
2. **possible_labware** (_dict_): a dictionary where every value is a dictionary containing a data frame corresponding to the values where _value_ will be searched and the labware associated with that data frame.

    The data frame containing the different values should be under the "Map Names" key, and the labware associated under the "Opentrons Place" key. In addition, the dictionary's values should have a third item with the key "Label" to recognize the item in case the _value_ is more than once in a specific data frame.

    For instance:
		
	   {1:{"Map Names":<class 'pandas.core.frame.DataFrame'>, "Opentrons Place":<class 'opentrons.protocol_api.labware.Labware'>, "Label":"abc"}, 2:{"Map Names":<class 'pandas.core.frame.DataFrame'>, "Opentrons Place":<class 'opentrons.protocol_api.labware.Labware'>, "Label":2}}

### Output

* An object from the class 'opentrons.protocol_api.labware.Well' corresponding to the well of the labware that the _value_ is in the data frame
* An exception in case the _value_ is not in the set of data frames or is more than 1 time in a data frame

### Summary of functioning

1. For loop through the values in _possible_labwares_
    1. Obtain the values of all cells with _value_. We will obtain a 'pandas.core.indexes.multi.MultiIndex' where every element is a tuple containing the dataframe cells where the value has been found. The first element of that touple will be the index of the cell and the second one the name of the column.
    2. Check how many elements the multi-index object has
    
        **0 element**
        1. Continue to the next element of _possible_labwares_
    
        **1 element**
        1. Return the well of the labware where the value has been found
    
        **> 1 element**
        1. Raise an exception
2. Reached the end of the for loop without going through step 1.ii.**1 element**.a so raise an exception of _value_ not found

## `generate_combinations_dict`

### Objective

A function that takes a specific type of data frame and converts it to a dictionary where the first column is the key, the second column will be
in the value "acceptor", and the rest of the values of the row are in the "module" value.

### Tested systems

Opentrons OT-2

### Requirements

* pandas package

### Input
1 input is needed:
1. **pd_combination** (_pandas.core.frame.DataFrame_): A pandas data frame must have at least 2 columns, the first one called "Name".
	
 	For instance:

    | Name | Acceptor Plasmid | Part 1 | Part 2 | Part 3 |
    | ---- | ---------------- | ------ | ------ | ------ |
    |Lv2-a1c1e1 | v_gB | pBadpTac-RBS_BCD12-GFPmut3-rpoC-g1R | pLacI-RBS_BCD12-araC-B0015_E1-g2 | pLacI-RBS_BCD12-LacI-rpoC-g3 |
    |Lv2-a1d1b1 | v_gB | pBadpTac-RBS_BCD12-GFPmut3-rpoC-g1R | pLacI-RBS_BCD12-LacI-rpoC-g2 | pLacI-RBS_BCD12-araC-B0015_E1-g3 |
    |Lv2-a2b2  |v_gA | pBad-RBS_BCD12-GFPmuy3-rpoC-g1R | pBad-RBS_BCD12-araC-B0015_E1-g2 |  |

### Output

* A dictionary in which the keys are the values of the column 'Name' of the _pd_combination_ and the values are another dictionary with 2 keys, 'acceptor' and 'modules'.
Each row of the _pd_combiantion_ will be one item of the dictionary.

	For instance:
		
	   {'Lv2-a1c1e1': {'acceptor': 'v_gB', 'modules': ['pBadpTac-RBS_BCD12-GFPmut3-rpoC-g1R', 'pLacI-RBS_BCD12-araC-B0015_E1-g2', 'pLacI-RBS_BCD12-LacI-rpoC-g3']}, 'Lv2-a1d1b1': {'acceptor': 'v_gB', 'modules': ['pBadpTac-RBS_BCD12-GFPmut3-rpoC-g1R', 'pLacI-RBS_BCD12-LacI-rpoC-g2', 'pLacI-RBS_BCD12-araC-B0015_E1-g3']}, 'Lv2-a2b2': {'acceptor': 'v_gA', 'modules': ['pBad-RBS_BCD12-GFPmuy3-rpoC-g1R', 'pBad-RBS_BCD12-araC-B0015_E1-g2']}}

### Summary of functioning

1. Get a list of the values of the column 'Name'
2. With a for-loop, go through all the values of the column 'Name'
	1. Get the elements of the row that has that name that is not a NaN value
	2. Add to the final dictionary (_combination_dict_) the item with the value of 'Name' as a key, the first element of the elements of that row under 'acceptor' and the rest under the key 'module'
3. Return the final dictionary _combination_dict_

## `generator_positions`

### Objective

Generator of the positions given in a list that will be given one by one when the function is called

### Tested systems

Opentrons OT-2

### Requirements

### Input

1 input is needed:
1. **labware_wells_name** (_list_): list of positions.

   For example:
      
       [A1 of Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2, A2 of Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2, A3 of Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2]

### Output

* The next element of the _labware_wells_name_

### Summary of functioning

1. For-loop of the elements in the _labware_wells_name_ list
	1. Yield the element of the list

## `mixing_eppendorf_15`

### Objective

A function that performs an extensive mixing with a pipette on a 1.5 mL Eppendorf located in a labware

### Tested systems

Opentrons OT-2

### Requirements

* `optimal_pipette_use` function
* `check_tip_and_pick` function
* `z_positions_mix` function
* NotSuitablePipette custom exception (included in the file)

### Input
5 inputs are required:
1. **location_tube** (_opentrons.protocol_api.labware.Well_): Well that will be mixed with a pipette.

   For example:
      
       B3 of Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap on 3
2. **volume_tube** (_float_): Volume that the _location_tube_ contains.

   For example:
      
       1200
3. **user_variables** (_custom class_): script class with attributes APINameTipR (name of the tiprack associated with the right mount pipette) and APINameTipL (name of the tiprack associated with the left mount pipette).

	For example:

	   class Example():
		  def __init__ (self):
               self.APINameTipR = opentrons_96_tiprack_20ul
               self.APINameTipL = opentrons_96_tiprack_300ul

4. **program_variables** (_custom class_):  script class with attributes pipR (pipette on the right mount), pipL (pipette on the left mount) and deckPositions (Dictionary with deck positions as keys and labware/module object as the value).

	For example:

	   class Example():
		  def __init__ (self):
                self.pipR = P20 Single-Channel GEN2 on right mount
		        self.pipL = P300 Single-Channel GEN2 on left mount
				self.deckPositions = {1: Opentrons 15 Tube Rack with Falcon 15 mL Conical on 1, 2: Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2, 3:None}

5. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)

### Output

 * The pipette used during the mixing
 
### Summary of functioning
1. Establish a volume that will be used to mix the _volume_tube_ of the _location_tube_
2. Try to establish the pipette that is going to perform the movements
	
 	**A pipette is established**
	1. Establish the maximum volume that the suitable pipette can aspirate
	2. Compare the max volume of the pipette with the mix Volume
		
  		_Mix volume > max volume pipette_
		1. Volume mixing is established as the max volume of the pipette
		
  		_Mix volume < max volume pipette_
		1. Volume mixing stays the same
	
 	**NotSuitablePipette exception is raised**
	1. Establish which pipette has the lowest minimum volume possible to aspirate
	2. Establish that pipette as the mixing pipette
3. Check if the mixing pipette has a tip
	
 	**No tip attached**
	1. Drop the tip if the other pipette has it
	2. Pick up a tip with the function `check_tip_and_pick`
4. Establish the positions where the pipette is going to move to aspirate and dispense with the function `z_positions_mix`
5. The pipette goes to the positions and aspirates and dispenses 7 times in the established mixing volume
6. Touch all sides of the _location_tube_ in different heights and with different radius
7. Aspirate from the first position and dispense in the last position twice
8. Aspirate from the last position and dispense in the first position twice
9. Blow out in the centre of the _location_tube_
10. Return the pipette that has been used to mix the _location_tube_

## `number_tubes_needed`

### Objective

A function that will return the number of tubes needed for a reactive and how many reactions can be distributed from every tube
	
This function does not guarantee the lower number of tubes, but it assures that everything can be picked with the pipettes associated if the _vol_reactive_per_reaction_factor_ can be picked with them.
	
### Tested systems

Opentrons OT-2

### Requirements

### Input
3 inputs needed:
1. **vol_reactive_per_reaction_factor** (_float_):  The volume of reactive/reaction

   For example:
      
       20
2. **number_reactions** (_integer_): Total number of reactions

   For example:
   
       200
3. **vol_max_tube** (_float_): Maximum volume of the tubes

   For example:
   
       2000
### Output
3 outputs:
* **number_tubes** (_integer_): final number of tubes that are needed

   For example:

       3
* **reactions_per_tube** (_list_): list of how many reactions per tube are holding the tubes

   For example:

       [67, 67, 66]
* **volumes_tubes** (_list_): volume of each tube

   For example:

       [1340, 1340, 1320]

### Summary of functioning
1. Initializing the values of the variables _number_tubes_, _reactions_per_tube_ and _volumes_tubes_
2. While loop checking that any of the tubes have more volume than the _vol_max_tube_
	1. Add 1 tube more
	2. Update the values of the variables _number_tubes_, _reactions_per_tube_ and _volumes_tubes_ to add that extra tube
3. Return the output variables

## `optimal_pipette_use`

### Objective

A function that will return the optimal pipette for the given volume.
	
If it is a greater volume than the maximum pipette volume, it will return the pipette that will give the minimal amount of movements to transfer the volume.
	
If none of the pipettes attached can pick the volume, the function will raise an error.

### Tested systems

Opentrons OT-2

### Requirements

* NotSuitablePipette custom exception (included in the file)

### Input
3 inputs are needed:
1. **aVolume** (_float_): volume that wants to be picked with the given pipettes

   For example:
   
       50
2. **pipette_r** (_opentrons.protocol_api.instrument_context.InstrumentContext_): attached right pipette

   For example:
       
       P20 Single-Channel GEN2 on right mount
3. **pipette_l** (_opentrons.protocol_api.instrument_context.InstrumentContext_): attached left pipette

   For example:
   
       P1000 Single-Channel GEN2 on left mount
### Output
* Pipette selected to handle the _aVolume_
* Exception in case there is no suitable pipette for the _aVolume_

### Summary of functioning
1. Check that there is a pipette attached

   **No pipette attached**
	1. Raise an exception

   **1 Pipette attached**
	1. Check the pipette attached can pick the volume
    	
    	_Left pipette attached and min volume is > aVolume_
		1. Return the left pipette
      	
      	_Right pipette attached and min volume is > aVolume_
		1. Return the right pipette
    	
    	_Pipette attached < aVolume_
    	1. Raise an exception

   **2 pipettes attached**
   1. Establish which pipette has the greater minimum volume
   2. Check if any pipette can aspirate the volume
   
      _Both pipettes can aspirate aVolume_
	  1. Return the greater minimum volume pipette
	
	  _One pipete can aspirate volume_
	  1. Return that pipette
 	
 	  _None of the pipettes can aspirate volume_
	  1. Raise an exception

## `position_dispense_aspirate_falcon15ml`

### Objective

A function that will return the height that the pipette should aspirate the volume without getting wet

The heights are measured manually.

### Tested systems

Opentrons OT-2

### Requirements

### Input
2 inputs are needed:
1. **vol_falcon** (_float_): Volume that the tube in the _theory_position_ has.

   For example:
   
       1000
2. **theory_position** (_opentrons.protocol_api.labware.Well_): Tube that is going to check and return the position of.

   For example:
   
       B1 of Opentrons 15 Tube Rack with Falcon 15 mL Conical on 2

### Output

* **final_position** (_opentrons.types.Location_): Location of the tube with the height position that the pipette is going to aspirate or dispense from given the _vol_falcon_

   For example:
       
       Location(point=Point(x=146.38, y=67.74, z=31.849999999999994)
### Summary of functioning
1. Check the volume that was given in _vol_falcon_
2. Assign the height measured for that volume
3. Return position with assigned height

## `run_program_thermocycler`

### Objective

A function that will read a table consisting of 4 columns: Temperature, Time (s), Number of Cycle and Cycle Status and will perform a temperature profile in an Opentrons thermocycler module.

### Tested systems

Opentrons OT-2

### Requirements

### Input
7 inputs are needed
1. **tc_mod** (_opentrons.protocol_api.module_contexts.ThermocyclerContext_)

   For example:
       
       ThermocyclerContext at Thermocycler Module GEN1 on 7 lw None
2. **program** (_pandas.core.frame.DataFrame_): Dataframe with 4 columns determining the steps and cycles the temperature profile will perform. Every row is a step of the profile.
   These are the columns:
   1. Temperature (_float_): The temperature, in centigrades, of this specific step
   2. Time (s) (_float_): The time, in seconds, that this specific step
   3. Number of cycles (_-|integer_): If the step is part of a cycle and the value of the column "Cycle Status" is set as _End_, this represents the number of times the cycle will be performed. Otherwise, this column should have a hyphen as a value.
   4. Cycle Status (_Start|End|-_): Variable that states which part of a cycle this step corresponds to. If the step is not the start or end of the cycle, it should have a hyphen as a value. Also, if the step is not inside a cycle, it should be filled with a hyphen.
      If the step is the first one of a cycle, this column should be filled with the value _Start_. If it is the last step of a cycle, the value should be _End_.

      For example:

        | Temperature | Time (s) | Number of cycles | Cycle status |
        | ----------- | -------- | ---------------- | ------------ |
        | 98 | 300 | - | - |
        | 98 | 10 | - | Start |
        | 30 | 30 | - | - |
        | 72 | 90 | 6 | End |
        | 98 | 10 | - | Start |
        | 45 | 30 | - | - |
        | 99 | 90 | 30 | End |
        | 72 | 300 | - | - |
4. **lid_temperature** (_float_): Value that will determine the value of the lid temperature during all the temperature profile.

   For example:
		
       100
5. **final_lid_state** (_boolean_): Value that determines if the lid of the module will be open (True) or closed (False) at the end of the temperature profile.

   For example:
	    
       True
6. **final_block_state** (_NaN|float_): Value that determines if the block temperature is set in a determined temperature after the performance of the temperature profile. If the value is NaN, the temperature block of the module will be deactivated. If this variable contains a number, the temperature block will be set as that value at the end of the profile.

   For example:
		
	   25
7. **volume_sample** (_float_): volume of the well that contains more liquid.
   
   For example:
		
  	   20
8. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)

### Output

* Performance of a temperature profile

### Summary of functioning
1. Set lid temperature
2. Go through all rows of the table _profile_
   1. Check the value of the column "Cycle Status"
      
      **Cycle Status is Start**
      1. Add the step to the cycle list
      2. State the _cycle_ variable as True
      3. Continue to the next row of the data frame
      
      **Cycle Status is End**
      1. Add the step to the cycle list
      2. Execute the cycle
      3. State the _cycle_ variable as False
      4. Continue to the next row of the data frame
   2. Check if the state of the variable _cycle_
      
      _cycle is True_
      1. Add the step to the cycle list
      
      _cycle is False_
      1. Execute the step with set_block_temperature
3. Deactivate the lid
4. If _final_lid_state_ is set as True, we open the lid
5. If _final_block_state_ is not empty, the block temperature is set as its value. If is empty, the temperature block is deactivated.

## `setting_labware`

### Objective

A function that will set a determined number of the same labware in free slots. Those slots will also be determined by a variable given, and if the labware cannot be loaded in any slot, an exception will be raised.

### Tested systems

Opentrons OT-2

### Requirements

### Input
5 inputs are required
1. **number_labware** (_integer_): Number of slots that the labware set in _labware_name_ will be defined if possible.

   For example:
       
       2
2. **labware_name** (_string_): API labware name that is going to be loaded in the deck.
   
   For example:
   
       opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap
3. **positions** (_dict_): Dictionary with the different slot places of the deck as keys and the values of the slot as values. If they are empty slots, the values should be None. Otherwise, the name of the labware that is occupying that slot.

   For example:
   
       {1: "opentrons_15_tuberack_falcon_15ml_conical",2: "armadillo_96_wellplate_200ul_pcr_full_skirt",3: None,4: "opentrons_96_tiprack_20ul"}
4. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)
5. **label** (_None|string|list_): names displayed in the final layout. The default value of this variable will be None, and no customized label will be set.

    For example:
		
		["Non-viscous reagents", "Viscous reagents"]

### Output
* **all_plates** (_dictionary_): Dictionary with the selected position as a key and the labware name defined as a value.

  For example:

       {3: biorad_96_wellplate_200ul_pcr}

### Summary of functioning
1. Set the items of _positions_ that have None as a value in a variable called _position_plates_
2. For loop through the number of _number_labware_ established
   1. The variable _labware_set_ is set as False
   2. Go through the _position_plates_
      1. Try to establish the labware with the set _label_
         
         **Successful load labware**
	     1. Load labware with _label_
     	 2. Add the labware and the position to the final output, _all_plates_
         3.  Set _labware_set_ as True
         4.  Break the for loop
	     
	     **DeckConflictError**
	     1. Continue to the next available position of _position_plates_
   3. Check if the variable _labware_set_ was established as True in the for loop
     
         _labware_set as false_
         1. Raise an exception
     
         _labware_set as true_
         1. Remove the position where the labware was established from _position_plates_
3. Return the list _all_plates_ with the positions as keys and the labware as values

## `tube_to_tube_transfer`

### Objective

A function destined to transfer a volume from 1 or more tubes with a volume associated with a set number of reactions to another tube or set of tubes with another set of reaction numbers

### Tested systems

Opentrons OT-2

### Requirements
* `check_tip_and_pick` function

### Input
8 inputs are needed
1. **vol_transfer_reaction** (_float_): volume per reaction that needs to be transferred from _positions_source_tubes_ to _positions_final_tubes_.

   For example:
   		
       25
3. **positions_source_tubes** (_list of opentrons.protocol_api.labware.Well'_): List of tube(s) that are going to be the source wells of the transfer

   For example:
   		
       [A1 of Opentrons 15 Tube Rack with Falcon 15 mL Conical on 2, B1 of Opentrons 15 Tube Rack with Falcon 15 mL Conical on 2]
5. **reactions_source_tubes** (_list of integers_): List of the reactions per tube that corresponds to the number of reactions that can be transferred to the _positions_final_tubes_

   For example:
   	
       [27, 27]
7. **positions_final_tubes** (_list of opentrons.protocol_api.labware.Well_): Final destination of the transfer from _posiions_source_tubes_

   For example:
		
		[A1 of Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap on 1, A2 of Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap on 1, A3 of Opentrons 24 Tube Rack with Eppendorf 1.5 mL Safe-Lock Snapcap on 1]
8. **reactions_final_tubes** (_list of integers_): Number of reactions of the volume _vol_transfer_reaction_ that need to be transferred to each tube from _positions_source_tubes_

   For example:
   		
       [18, 18, 18]
10. **user_variables** (_custom class_): script class with attributes APINameTipR (name of the tiprack associated with the right mount pipette), APINameTipL (name of the tiprack associated with the left mount pipette), startingTipPipR (the first tip that the right pipette should pick) and startingTipPipL (the first tip that the left pipette should pick).

	For example:

	    class Example():
		  	def __init__ (self):
                self.APINameTipR = opentrons_96_tiprack_20ul
                self.APINameTipL = opentrons_96_tiprack_300ul
                self.startingTipPipR = "A1"
                self.startingTipPipL = "B3"
				
11. **program_variables** (_custom class_):  script class with the attribute deckPositions (Dictionary with deck positions as keys and labware/module object as the value).

	For example:

		class Example():
		  	def __init__ (self):
				self.deckPositions = {1: Opentrons 15 Tube Rack with Falcon 15 mL Conical on 1, 2: Armadillo 96 Well Plate 200 µL PCR Full Skirt on 2, 3:None}
12. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)

### Output

* Volume transferred from a set of wells to another set of wells

### Summary of functioning

1. 

## `vol_distribute_2pips`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `wells_selection`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `z_positions_mix`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

# Function Leyend
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
1. **pipette\_used** (_opentrons.protocol_api.instrument_context.InstrumentContext_): For example:
        
        P20 Single-Channel GEN2 on right mount object
2. **position\_deck** (_dictionary_): Dictionary with deck positions as keys and labware/module object as the value. For example:

        {1: Opentrons 96 Tip Rack 20 µL on 1, 2: Opentrons 96 Tip Rack 20 µL on 2, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None, 11: None}
3. **variables\_define\_tiprack** (_class_): script class with attributes APINameTipR (name of the tiprack associated with the right mount pipette) and APINameTipL (name of the tiprack associated with the left mount pipette). For example:

        class Example():
            def __init__ (self):
                self.APINameTipR = opentrons_96_tiprack_20ul
                self.APINameTipL = opentrons_96_tiprack_300ul
4. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)
	 
### Output
* The dictionary _position_deck_ will be updated to have the new tiprack
* The provided pipette will pick up a tip
	
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

Function that will define a tiprack associated with a pipette in an available position that does not raise a space conflict error

This function is used in the function `check_tip_and_pick`

### Tested systems

Opentrons OT-2

### Requirements
* Error DeckConflictError from the package opentrons

### Input
4 Inputs required:
1. **pipette** (_opentrons.protocol_api.instrument_context.InstrumentContext_): For example:
        
        P20 Single-Channel GEN2 on right mount object
2. **position_deck** (_dictionary_): Dictionary with deck positions as keys and labware/module object as the value. For example:

        {1: Opentrons 96 Tip Rack 20 µL on 1, 2: Opentrons 96 Tip Rack 20 µL on 2, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None, 11: None}
3. **variables_define_tiprack** (_class_): script class with attributes APINameTipR (name of the tiprack associated with right mount pipette) and APINameTipL (name of the tiprack associated with left mount pipette). For example:

        class Example():
            def __init__ (self):
                self.APINameTipR = opentrons_96_tiprack_20ul
                self.APINameTipL = opentrons_96_tiprack_300ul
5. **protocol** (_opentrons.protocol_api.protocol_context.ProtocolContext_)

### Output

* Dictionary with the selected position as a key and the tiprack defined as a value. For example:

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

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `find_well_by_value`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `generate_combinations_dict`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `generator_positions`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `mixing_eppendorf_15`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `number_tubes_needed`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `optimal_pipette_use`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `position_dispense_aspirate_falcon15ml`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `run_program_thermocycler`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `setting_labware`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

## `tube_to_tube_transfer`

### Objective

### Tested systems

Opentrons OT-2

### Requirements

### Input

### Output

### Summary of functioning

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

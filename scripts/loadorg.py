"""
Load simulation parameters from each organism species config file.
"""

import configparser
import os, glob

# Find organism filenames
org_files = glob.glob('./*.org')

# Initialize list of dictionaries to hold all organism parameters
# Each dictionary contains parameters for a single species
org_dict_list = []
for org_file in org_files:
    # Initialize temporary dict to store species parameters
    org_dict = {}

    # Parameters that must be str
    param_str = ['species_name', 'movement_type', 'food_intake_prescription', 'reproduction_type']

    # Parameters that must be int
    param_int = ['population_size', 'dna_length']

    # Parameters that must be int or 'none'
    param_int_none = ['max_age', 'max_time_without_food', 'max_time_without_water', 'mutation_rate',
                      'food_capacity', 'food_initial', 'food_metabolism', 'food_intake', 
                      'water_capacity', 'water_initial', 'water_metabolism', 'water_intake']

    # Parameters that must be bool
    param_bool = ['can_mutate']

    # Load from config file
    config_org = configparser.ConfigParser()
    config_org.read(org_file)

    # Cycle through all parameters in the config file, 
    # converting them to proper types as specifed above
    for section in config_org.sections():
        for key in config_org[section]:
            temp_param = config_org[section][key]

            if key in param_str:
                pass
            elif key in param_int:
                temp_param = int(temp_param)
            elif key in param_int_none:
                if temp_param != 'none':
                    temp_param = int(temp_param)
            elif key in param_bool:
                temp_param = (temp_param == 'True')
            else:
                raise NameError('Key is not a valid parameter')
            org_dict(key) = temp_param

    org_dict_list.append(org_dict)

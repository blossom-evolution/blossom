"""Load simulation parameters from each organism species config file.

This module loads simulation parameters from a world configuration file in the
same directory. 

Attributes:
    attribute1 (type1): description1

Todo:
    * For module TODOs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import configparser
import os, glob

# Find organism filenames
org_files = glob.glob('*.org')

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

    # Parameters that must be int or 'None'
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
        for (key,val) in config_org.items(section):

            if key in param_str:
                pass
            elif key in param_int:
                val = int(val)
            elif key in param_int_none:
                if val != 'None':
                    val = int(val)
            elif key in param_bool:
                val = (val == 'True')
            else:
                raise NameError('Key is not a valid parameter')
            
            if val == 'None':
                val = None
            org_dict[key] = val

    org_dict_list.append(org_dict)

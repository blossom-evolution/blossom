"""
Built-in dictionaries with world, species, and organism parameters (or fields).

Both Organism and World objects are initialized based on these field
dictionaries, and values are either populated from parameter files or take
on the default values specified in this module.
"""

world_field_names = {'dimensionality': 1,
                     'world_size': [10],
                     'initial_environment_dict': None,
                     'water': None,
                     'food': None,
                     'obstacles': None}

specific_organism_field_names = {'organism_id': None,
                                 'dna': '0000',
                                 'age': 0,
                                 'alive': True,
                                 'age_at_death': None,
                                 'cause_of_death': None,
                                 'position': [0],
                                 'sex': None,
                                 'ancestry': [],
                                 'custom_methods_fns': None,
                                 'water_current': None,
                                 'time_without_water': 0,
                                 'food_current': None,
                                 'time_without_food': 0}

species_field_names = {'species_name': 'species1',
                       'movement_type': 'stationary',
                       'reproduction_type': None,
                       'drinking_type': None,
                       'eating_type': None,
                       'action_type': 'move_only',
                       'dna_length': 4,
                       'max_age': 20,
                       'max_time_without_food': None,
                       'max_time_without_water': None,
                       'mutation_rate': None,
                       'food_capacity': None,
                       'food_initial': None,
                       'food_metabolism': None,
                       'food_intake': None,
                       'water_capacity': None,
                       'water_initial': None,
                       'water_metabolism': None,
                       'water_intake': None}

# Combine organism and species field names
organism_field_names = dict(specific_organism_field_names,
                            **species_field_names)

"""
Fields + defaults
"""

world_field_names = {'dimensionality': 1,
                     'world_size': [10],
                     'environment_filename': None}

specific_organism_field_names = {'organism_id': None,
                        'dna': '0000',
                        'age': 0,
                        'alive': True,
                        'position': [0],
                        'sex': None,
                        'water_current': None,
                        'food_current': None}

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

organism_field_names = dict(specific_organism_field_names, **species_field_names)

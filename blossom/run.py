"""
This should probably have stuff in it, unclear what exactly yet.
"""

# import loadenv, loadorg

class BaseOrganism(object):
    """ Create a base organism structure for all species """

    def __init__(self, **kwargs):
        """ Create a new organism with arguments based on the species
            parameter files """

        prop_defaults = {
            'species_name': 'species1',
            'population_size': 2,
            'dna_length': 4,
            'movement_type': 'simple_random',
            'max_age': 20,
            'max_time_without_food': None,
            'max_time_without_water': None,
            'can_mutate': False,
            'mutation_rate': None,
            'food_intake_prescription': None,
            'food_capacity': None,
            'food_initial': None,
            'food_metabolism': None,
            'food_intake': None,
            'water_capacity': None,
            'water_initial': None,
            'water_metabolism': None,
            'water_intake': None,
            'repoduction_type': 'pure_replication'
        }

        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))

        self.age = 0

if __name__ == '__main__':
    # execute code here
    organism1 = BaseOrganism()
    print('The organism\'s current age is', organism1.age)
    pass

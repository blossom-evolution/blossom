import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import blossom

WORLD_FN = None
ORGANISMS_FN = None
WORLD_PARAM_FN = 'world.param'
SPECIES_PARAM_FNS = ['species1.param']
CUSTOM_METHODS_FNS = ['custom_methods.py']
DATASET_OUTPUT_DIR = 'datasets/test_general/'

START_TIME = 0
END_TIME = 100

world_size = 100
world_block = world_size // 5

peak_water = 10000
water = [peak_water] * (world_size // 2) + [0] * (world_size // 2)
water = [0] * world_block + [peak_water] * world_block * 2 + [0] * world_block * 2

peak_food = 10000
food = [0] * (world_size // 2) + [peak_food] * (world_size // 2)
food = [0] * world_block * 2 + [peak_water] * world_block * 2 + [0] * world_block

blossom.write_environment(water,
                          food,
                          [0] * world_size,
                          'generated_environment.json')
# blossom.write_environment([0] * (world_size // 4) + [500] * (world_size // 4) + [1000] * (world_size // 4) + [2000] * (world_size // 4),
#                           [0] * world_size,
#                           [0] * world_size,
#                           'generated_environment.json')

universe = blossom.Universe(world_fn=WORLD_FN,
                            organisms_fn=ORGANISMS_FN,
                            world_param_fn=WORLD_PARAM_FN,
                            species_param_fns=SPECIES_PARAM_FNS,
                            custom_methods_fns=CUSTOM_METHODS_FNS,
                            current_time=START_TIME,
                            end_time=END_TIME,
                            dataset_dir=DATASET_OUTPUT_DIR)
while universe.current_time < universe.end_time:
    print('t = %s: %s organisms' % (universe.current_time, len(universe.organism_list)))
    universe.step()

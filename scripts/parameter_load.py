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
blossom.write_environment([100000] * world_size,
                          [0] * world_size,
                          [0] * world_size,
                          'generated_environment.json')

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

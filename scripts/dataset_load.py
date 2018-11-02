import blossom

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

WORLD_FN = 'datasets/world_ds0010.txt'
ORGANISMS_FN = 'datasets/organisms_ds0010.txt'
WORLD_PARAM_FN = None
SPECIES_PARAM_FNS = None
CUSTOM_METHODS_FNS = None
DATASET_OUTPUT_DIR = 'datasets/test_general/'

START_TIME = 0
END_TIME = 100

universe = blossom.Universe(world_fn=WORLD_FN,
                            organisms_fn=ORGANISMS_FN,
                            world_param_fn=WORLD_PARAM_FN,
                            species_param_fns=SPECIES_PARAM_FNS,
                            current_time=START_TIME,
                            end_time=END_TIME)

while universe.current_time < universe.end_time:
    universe.step()

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))

import blossom

WORLD_FN = None
ORGANISM_FNS = None
WORLD_PARAM_FN = 'world.env'
SPECIES_PARAM_FNS = ['species1.org']
START_TIME = 0
END_TIME = 10

universe = blossom.Universe(world_fn=WORLD_FN,
                            organism_fns=ORGANISM_FNS,
                            world_param_fn=WORLD_PARAM_FN,
                            species_param_fns=SPECIES_PARAM_FNS,
                            current_time=START_TIME,
                            end_time=END_TIME)
while universe.current_time < universe.end_time:
    universe.step()

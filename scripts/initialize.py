import sys
import os
sys.path.append(os.path.dirname(__file__) + "/..")

import blossom

WORLD_PARAM_FN = "world.env"
SPECIES_PARAM_FNS = ["species1.org"]
INITIAL_TIME = 0

universe = blossom.Universe(world_param_fn=WORLD_PARAM_FN,species_param_fs=SPECIES_PARAM_FNS)

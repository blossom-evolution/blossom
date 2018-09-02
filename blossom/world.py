import json
import numpy as np

import fields

class World(object):
    """
    World class for the environment of the simulation.
    """

    def __init__(self, init_dict={}):
        # Sets up defaults based on world parameters
        for (prop, default) in fields.world_field_names.items():
            setattr(self, prop, init_dict.get(prop, default))

        # self.water = self.initial_environment_dict['water']
        # self.food = self.initial_environment_dict['food']
        # self.obstacles = self.initial_environment_dict['obstacles']

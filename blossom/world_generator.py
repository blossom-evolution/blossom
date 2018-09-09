import numpy as np
import sys
import json

def write_environment(water, food, obstacles, environment_fn='environment.json'):
    if len(water) != len(food) or len(water) != len(obstacles):
        sys.exit('Invalid environment arrays!')
    env_dict = {'water': water,
                'food': food,
                'obstacles': obstacles}
    with open(environment_fn, 'w') as f:
        json.dump(env_dict, f)

def constant_list(val, length):
    return [val] * length

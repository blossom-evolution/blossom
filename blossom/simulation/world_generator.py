import sys
import json


def write_environment(water,
                      food,
                      obstacles,
                      environment_fn='environment.json'):
    """
    Write water, food, and obstacles lists to an environment file.
    """
    if len(water) != len(food) or len(water) != len(obstacles):
        sys.exit('Invalid environment arrays!')
    env_dict = {'water': water,
                'food': food,
                'obstacles': obstacles}
    with open(environment_fn, 'w') as f:
        json.dump(env_dict, f)


def constant_list(val, length):
    """
    Generate a constant-valued list.
    """
    return [val] * length


def constant_2d_list(val, size):
    """
    Generate a constant-valued two dimensional array.
    """
    return [constant_list(val, size[1]) for i in size[0]]

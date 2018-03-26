"""Load simulation parameters from world config file.

This module loads simulation parameters from a world configuration file in the
same directory.

Attributes:
    dimensionality (int): Usually should be 1, 2, or 3. Specifies the
        dimensionality of the world and therefore how many degrees of freedom
        organism movement can take.
    world_size (list, or 'none'): Depending on

Todo:
    * For module TODOs

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import configparser
import os, glob

env_file = glob.glob('*.env')
if len(env_file) == 0:
    raise IndexError('There is no environment configuration file in the '
        + 'current directory.')
if len(env_file) > 1:
    print('There are multiple environment configuration files in the current '
        + 'directory. There should only be one environment configuration file. '
        + 'Selecting one at random.')
env_file = env_file[0]

# Load from config file
config_world = configparser.ConfigParser()
config_world.read(env_file)

# dimensionality: int
dimensionality = int(config_world.get('Overall Parameters', 'dimensionality'))

# world_size: space delimited ints in agreement with dimensionality, or 'None'
# example: world_size = 10 10
world_size = config_world.get('Overall Parameters', 'world_size')
if world_size == 'None':
    world_size = None
else:
    world_size = [int(L) for L in world_size.split()]

# environment_filename: str, or 'None'
environment_filename = config_world.get('Overall Parameters',
                                        'environment_filename')
if environment_filename == 'None':
    environment_filename = None

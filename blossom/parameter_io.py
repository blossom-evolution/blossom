"""
Load information from parameter files and construct world and
organism objects at the initial timestep.
"""

import glob
import configparser
import json
import random
import copy

from utils import cast_to_list
from world import World
from organism import Organism


def load_world_parameters(fn):
    """
    Load world parameter file and construct initial World object.

    Parameters
    ----------
    fn : str
        Input filename of parameter file.

    Returns
    -------
    world : World
        World object constructed from the parameter file.
    """

    env_file = glob.glob(fn)
    if len(env_file) == 0:
        raise IndexError('There is no environment configuration file in the '
                         + 'current directory.')
    if len(env_file) > 1:
        print('There are multiple environment configuration files in the '
              + 'current directory. There should only be one environment '
              + 'configuration file. Selecting the first provided..')
    env_file = env_file[0]

    world_dict = {}
    # Load from config file
    config_world = configparser.ConfigParser()
    config_world.read(env_file)

    # environment_filename: str, or 'None'
    environment_filename = config_world.get('Overall Parameters',
                                            'environment_filename')
    if environment_filename != 'None':
        with open(environment_filename, 'r') as f:
            initial_environment_dict = json.load(f)

        world_dict['water'] = initial_environment_dict['water']
        world_dict['food'] = initial_environment_dict['food']
        world_dict['obstacles'] = initial_environment_dict['obstacles']

        if type(world_dict['water'][0]) is list:
            world_dict['dimensionality'] = 2
            world_dict['world_size'] = [len(world_dict['water']),
                                        len(world_dict['water'][0])]
        else:
            world_dict['dimensionality'] = 1
            world_dict['world_size'] = [len(world_dict['water'])]

    else:
        # world_size: space delimited ints, or 'None'
        # example: world_size = 10 10
        world_size = config_world.get('Overall Parameters', 'world_size')
        if world_size == 'None':
            # this is probably harder to do,
            # since we'd have to allow for infinite bounds...
            world_size = None
            return -1
        else:
            world_size = [int(L) for L in world_size.split()]
            world_dict['world_size'] = world_size
            world_dict['dimensionality'] = len(world_size)

            if len(world_size) == 2:
                blank_vals = [[0 for x in range(world_size[1])]
                              for x in range(world_size[0])]
            elif len(world_size) == 1:
                blank_vals = [0 for x in range(world_size)[0]]
            else:
                raise ValueError

            world_dict['water'] = copy.deepcopy(blank_vals)
            world_dict['food'] = copy.deepcopy(blank_vals)
            world_dict['obstacles'] = copy.deepcopy(blank_vals)

    return World(world_dict)


def load_species_parameters(fns, init_world, custom_methods_fns):
    """
    Load all available species parameter files.

    Parameters
    ----------
    fns : list of str
        Input filenames of species parameter files. Different species get
        different species parameter files, from which the individual organisms
        are initialized.
    init_world : World
        Initial World instance for this Universe.
    custom_methods_fns : list of str
        List of external Python scripts containing custom organism
        behaviors. :mod:`blossom` will search for methods within each
        filename included here.

    Returns
    -------
    organism_list : list of Organisms
        A list of Organism objects constructed from the parameter file.

    """

    # Find organism filenames, can be a list of patterns
    fns = cast_to_list(fns)
    org_files = [fn for pattern in fns for fn in glob.glob(pattern)]

    # Initialize list of dictionaries to hold all organism parameters
    # Each dictionary contains parameters for a single species
    organism_list = []
    for org_file in org_files:
        # Initialize temporary dict to store species parameters
        organism_dict = {}

        # Parameters that must be str
        param_str = ['species_name',
                     'movement_type',
                     'reproduction_type',
                     'drinking_type',
                     'action_type',
                     'eating_type']

        # Parameters that must be int
        param_int = ['population_size',
                     'dna_length',
                     'max_age']

        # Parameters that must be int or 'None'
        param_int_none = ['max_time_without_food',
                          'max_time_without_water',
                          'mutation_rate',
                          'food_capacity',
                          'food_initial',
                          'food_metabolism',
                          'food_intake',
                          'water_capacity',
                          'water_initial',
                          'water_metabolism',
                          'water_intake']

        # Parameters that must be float
        param_float = ['proportion_m',
                       'proportion_f',
                       'proportion_a',
                       'proportion_h']

        # Parameters that must be bool
        param_bool = ['can_mutate']

        # Load from config file
        config_org = configparser.ConfigParser()
        config_org.read(org_file)

        # Cycle through all parameters in the config file,
        # converting them to proper types as specifed above
        for section in config_org.sections():
            for (key, val) in config_org.items(section):

                if key in param_str:
                    pass
                elif key in param_int:
                    val = int(val)
                elif key in param_int_none:
                    if val != 'None':
                        val = int(val)
                elif key in param_float:
                    val = float(val)
                elif key in param_bool:
                    val = (val == 'True')
                else:
                    print(key, val)
                    raise NameError('Key is not a valid parameter')
                # ensure 'None' parameters are set to None
                if val == 'None':
                    val = None
                organism_dict[key] = val

        # Track custom method file paths
        organism_dict['custom_methods_fns'] = custom_methods_fns

        # Generate all organisms
        for i in range(organism_dict['population_size']):
            # Vary organism location randomly
            position = []
            for i in range(init_world.dimensionality):
                position.append(random.randrange(0, init_world.world_size[i]))
            organism_dict['position'] = position

            # Add organism to organism list
            organism_list.append(Organism(organism_dict))

        return organism_list

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
import fields


def load_world(fn=None, init_dict={}):
    """
    Load world from either parameter file or dictionary and construct
    initial World object.

    Parameters
    ----------
    fn : str
        Input filename of parameter file.
    init_dict : dict
        Dictionary containing world parameters.

    Returns
    -------
    world : World
        World object constructed from the parameter file.
    """
    if fn:
        return load_world_from_param_file(fn)
    else:
        return load_world_from_dict(init_dict)


def load_world_from_dict(init_dict):
    world_init_dict = {}
    for (prop, default) in fields.world_field_names.items():
        world_init_dict[prop] = init_dict.get(prop, default)

    # Check world size parameters, set dimensionality value accordingly
    assert type(world_init_dict['world_size']) is list
    assert len(world_init_dict['world_size']) <= 2
    world_init_dict['dimensionality'] = len(world_init_dict['world_size'])
    for i in world_init_dict['world_size']:
        assert type(i) is int

    # Check that field list sizes are consistent with each other
    field_lengths = []
    field_names = []
    for field in ['water', 'food', 'obstacles']:
        if world_init_dict[field]:
            assert type(world_init_dict[field]) is list
            # Check each element of these fields is either int or float (can
            # include math.inf, which is a float)
            for i in world_init_dict[field]:
                if type(i) is list:
                    for j in i:
                        assert type(j) in [int, float]
                else:
                    assert type(i) in [int, float]
            field_lengths.append(len(world_init_dict[field]))
            field_names.append(field)
    if len(field_lengths) >= 2:
        assert field_lengths[0] == field_lengths[1]
    if len(field_lengths) == 3:
        assert field_lengths[1] == field_lengths[2]

    # Check that field list sizes are consistent with the world size
    if len(field_names) >= 1:
        field = field_names[0]
        assert world_init_dict['world_size'][0] == len(world_init_dict[field])
        if len(field) == 2:
            assert world_init_dict['world_size'][1] \
                == len(world_init_dict[field][0])

    return World(world_init_dict)


def load_world_from_param_file(fn):
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

    world_init_dict = {}
    # Load from config file
    config_world = configparser.ConfigParser()
    config_world.read(env_file)

    # environment_filename: str, or 'None'
    environment_filename = config_world.get('Overall Parameters',
                                            'environment_filename')
    if environment_filename != 'None':
        with open(environment_filename, 'r') as f:
            initial_environment_dict = json.load(f)

        world_init_dict['water'] = initial_environment_dict['water']
        world_init_dict['food'] = initial_environment_dict['food']
        world_init_dict['obstacles'] = initial_environment_dict['obstacles']

        if type(world_init_dict['water'][0]) is list:
            world_init_dict['dimensionality'] = 2
            world_init_dict['world_size'] = [len(world_init_dict['water']),
                                        len(world_init_dict['water'][0])]
        else:
            world_init_dict['dimensionality'] = 1
            world_init_dict['world_size'] = [len(world_init_dict['water'])]

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
            world_init_dict['world_size'] = world_size
            world_init_dict['dimensionality'] = len(world_size)

            if len(world_size) == 2:
                blank_vals = [[0 for x in range(world_size[1])]
                              for x in range(world_size[0])]
            elif len(world_size) == 1:
                blank_vals = [0 for x in range(world_size)[0]]
            else:
                raise ValueError

            world_init_dict['water'] = copy.deepcopy(blank_vals)
            world_init_dict['food'] = copy.deepcopy(blank_vals)
            world_init_dict['obstacles'] = copy.deepcopy(blank_vals)

    return World(world_init_dict)


def create_organisms(species_init_dict,
                     init_world=World({}),
                     position_callback=None):
    '''
    Make organism list from an species_init_dict either provided directly or
    scraped from parameter file.
    '''
    organism_list = []
    list_field_keys = []
    for key in species_init_dict.keys():
        if type(species_init_dict[key]) is list:
            if key != 'custom_methods_fns':
                list_field_keys.append(key)
    # Generate all organisms
    for i in range(species_init_dict['population_size']):
        organism_init_dict = copy.deepcopy(species_init_dict)
        for key in list_field_keys:
            organism_init_dict[key] = organism_init_dict[key][i]
        if 'initial_positions' in species_init_dict.keys():
            position = organism_init_dict['initial_positions']
        elif position_callback:
            position = position_callback(init_world.world_size)
        elif 'position_callback' in species_init_dict.keys():
            position = (species_init_dict['position_callback']
                        (init_world.world_size))
        else:
            # Vary organism location randomly
            position = []
            for i in range(init_world.dimensionality):
                position.append(random.randrange(0,
                                                 init_world.world_size[i]))
        organism_init_dict['position'] = position

        # Add organism to organism list
        organism_list.append(Organism(organism_init_dict))

    return organism_list


def load_species(fns=None,
                 init_dicts=[{}],
                 init_world=World({}),
                 custom_methods_fns=[]):
    """
    Load organisms from available species parameter files or dictionaries.

    Parameters
    ----------
    fns : list of str
        Input filenames of species parameter files. Different species get
        different species parameter files, from which the individual organisms
        are initialized.
    init_dicts : list of dict
        Parameter dicts for each species.
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
    if fns:
        return load_species_from_param_files(fns,
                                             init_world,
                                             custom_methods_fns)
    else:
        return load_species_from_dict(init_dicts,
                                      init_world,
                                      custom_methods_fns)


def load_species_from_dict(init_dicts,
                           init_world,
                           custom_methods_fns=None):
    """
    Create a list of organisms loaded from Python dicts.

    Parameters
    ----------
    init_dicts : list of dict
        Input species dictionaries from which the individual organisms
        are initialized. Each dictionary is for a different species.
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

    init_dicts = cast_to_list(init_dicts)

    organism_list = []
    for init_dict in init_dicts:

        species_init_dict = {}
        for (prop, default) in fields.species_field_names.items():
            species_init_dict[prop] = init_dict.get(prop, default)

        assert 'population_size' in init_dict.keys()
        population_size = init_dict['population_size']
        assert type(population_size) is int
        species_init_dict['population_size'] = population_size

        assert type(species_init_dict['species_name']) == str

        for field in ['movement_type',
                      'reproduction_type',
                      'drinking_type',
                      'eating_type',
                      'action_type']:
            assert (species_init_dict[field] is None
                    or type(species_init_dict[field]) is str)

        for field in ['dna_length']:
            assert type(species_init_dict[field]) is int

        if species_init_dict['drinking_type']:
            assert (
                species_init_dict['water_capacity'] is not None
                and species_init_dict['water_initial'] is not None
                and species_init_dict['water_metabolism'] is not None
                and species_init_dict['water_intake'] is not None
                and species_init_dict['max_time_without_water'] is not None
            )
        if species_init_dict['eating_type']:
            assert (
                species_init_dict['food_capacity'] is not None
                and species_init_dict['food_initial'] is not None
                and species_init_dict['food_metabolism'] is not None
                and species_init_dict['food_intake'] is not None
                and species_init_dict['max_time_without_food'] is not None
            )

        for field in ['max_age',
                      'max_time_without_food',
                      'max_time_without_water',
                      'mutation_rate',
                      'food_capacity',
                      'food_initial',
                      'food_metabolism',
                      'food_intake',
                      'water_capacity',
                      'water_initial',
                      'water_metabolism',
                      'water_intake']:
            if type(species_init_dict[field]) is list:
                assert (len(species_init_dict[field]) == population_size)
            elif type(species_init_dict[field]) in [int, float]:
                species_init_dict[field] = ([species_init_dict[field]]
                                            * population_size)
            else:
                assert species_init_dict[field] is None

        if not species_init_dict['custom_methods_fns']:
            # Track custom method file paths
            species_init_dict['custom_methods_fns'] = custom_methods_fns

        if 'initial_positions' in init_dict.keys():
            assert len(init_dict['initial_positions']) == population_size
            for position in init_dict['initial_positions']:
                assert len(position) == init_world.dimensionality
            species_init_dict['initial_positions'] \
                = init_dict['initial_positions']

        organism_list.extend(create_organisms(species_init_dict, init_world))

    return organism_list


def load_species_from_param_files(fns,
                                  init_world,
                                  custom_methods_fns=None):
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
    for i, org_file in enumerate(org_files):
        # Initialize temporary dict to store species parameters
        species_init_dict = {}

        # Parameters that must be str or None
        param_str = ['species_name',
                     'movement_type',
                     'reproduction_type',
                     'drinking_type',
                     'action_type',
                     'eating_type']

        # Parameters that must be int
        param_int = ['population_size',
                     'dna_length']

        # Parameters that must be int or 'None' or 'inf'
        param_int_none_inf = ['max_age',
                              'max_time_without_food',
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
                elif key in param_int_none_inf:
                    if val != 'None' and type(val) not in [int, float]:
                        val = float(val)
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
                species_init_dict[key] = val

        # Track custom method file paths
        species_init_dict['custom_methods_fns'] = custom_methods_fns

        organism_list.extend(create_organisms(species_init_dict,
                                              init_world))

    return organism_list

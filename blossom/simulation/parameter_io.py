"""
Load information from parameter files and construct world and
organism objects at the initial timestep.
"""

import glob
import configparser
import yaml
import json
import numpy as np
import copy

from .utils import cast_to_list
from .world import World
from .organism import Organism
from . import default_fields


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
    for (field, default) in default_fields.world_fields.items():
        world_init_dict[field] = init_dict.get(field, default)
    # Check world size parameters, set dimensionality value accordingly
    if type(world_init_dict['world_size']) is int:
        world_init_dict['world_size'] = [world_init_dict['world_size']]
    else:
        assert type(world_init_dict['world_size']) is list
        assert len(world_init_dict['world_size']) <= 2
    world_init_dict['dimensionality'] = len(world_init_dict['world_size'])
    for i in world_init_dict['world_size']:
        assert type(i) is int

    # Check that field list sizes are consistent with each other
    field_lengths = []
    fields = []
    for field in ['water', 'food', 'obstacles']:
        if world_init_dict[field] is not None:
            field_lengths.append(len(world_init_dict[field]))
            fields.append(field)
    if len(field_lengths) >= 2:
        assert field_lengths[0] == field_lengths[1]
    if len(field_lengths) == 3:
        assert field_lengths[1] == field_lengths[2]

    # Check that field list sizes are consistent with the world size
    if len(fields) >= 1:
        field = fields[0]
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


def load_species(fns=None,
                 init_dicts=[{}],
                 init_world=World({}),
                 custom_module_fns=[]):
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
    custom_module_fns : list of str
        List of external Python scripts containing custom organism
        behaviors. :mod:`blossom` will search for methods within each
        filename included here.

    Returns
    -------
    population_dict : dict of Organisms
        A dict of Organism objects constructed from the parameter file.

    """
    if fns:
        return load_species_from_param_files(fns,
                                             init_world,
                                             custom_module_fns)
    else:
        return load_species_from_dict(init_dicts,
                                      init_world,
                                      custom_module_fns)


def create_organisms(species_init_dict,
                     init_world=World({}),
                     location_callback=None,
                     seed=None):
    '''
    Make organism list from an species_init_dict either provided directly or
    scraped from parameter file. All organisms are from a single species.
    '''
    rng = np.random.default_rng(seed)

    organism_list = []
    list_field_keys = []
    for key in species_init_dict.keys():
        if type(species_init_dict[key]) is list:
            if key != 'custom_module_fns':
                list_field_keys.append(key)

    # Generate all organisms
    initial_population = species_init_dict['population_size']
    for i in range(initial_population):
        organism_init_dict = {
            key: val for key, val in species_init_dict.items()
            if not key == 'population_size'
        }

        for key in list_field_keys:
            organism_init_dict[key] = organism_init_dict[key][i]
        if 'initial_locations' in species_init_dict:
            location = organism_init_dict['initial_locations']
        elif location_callback:
            location = location_callback(init_world.world_size)
        elif 'location_callback' in species_init_dict:
            location = (species_init_dict['location_callback']
                        (init_world.world_size))
        else:
            # Vary organism location randomly
            location = []
            for i in range(init_world.dimensionality):
                location.append(rng.integers(0, init_world.world_size[i]))
        organism_init_dict['location'] = location

        # Add organism to organism list
        organism_list.append(Organism(organism_init_dict, seed=seed))

    return organism_list


def load_species_from_dict(init_dicts,
                           init_world,
                           custom_module_fns=None,
                           seed=None):
    """
    Create a list of organisms loaded from Python dicts.

    Parameters
    ----------
    init_dicts : list of dict
        Input species dictionaries from which the individual organisms
        are initialized. Each dictionary is for a different species.
    init_world : World
        Initial World instance for this Universe.
    custom_module_fns : list of str
        List of external Python scripts containing custom organism
        behaviors. :mod:`blossom` will search for methods within each
        filename included here.
    seed : int, Generator, optional
        Random seed for the simulation

    Returns
    -------
    population_dict : dict of Organisms
        A dict of Organism objects constructed from the parameter file.

    """
    init_dicts = cast_to_list(init_dicts)

    population_dict = {}
    for init_dict in init_dicts:
        species_init_dict = {}

        # Set up defaults based on species parameters
        for (field, default) in default_fields.species_fields.items():
            species_init_dict[field] = init_dict.get(field, default)

        # Set up custom fields provided in initialization dictionary
        init_keys = set(init_dict.keys())
        default_keys = set(default_fields.species_fields.keys())
        for custom_field in (init_keys - default_keys):
            species_init_dict[custom_field] = init_dict[custom_field]

        assert 'population_size' in init_dict
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

        if not species_init_dict['custom_module_fns']:
            # Track custom method file paths
            species_init_dict['custom_module_fns'] = custom_module_fns

        if 'initial_locations' in init_dict:
            assert len(init_dict['initial_locations']) == population_size
            for location in init_dict['initial_locations']:
                assert len(location) == init_world.dimensionality
            species_init_dict['initial_locations'] \
                = init_dict['initial_locations']

        species_organism_list = create_organisms(species_init_dict, init_world, seed=seed)

        # Populate population dict with relevant bulk stats and organism lists
        population_dict[species_init_dict['species_name']] = {
            'statistics': {
                'total': population_size,
                'alive': population_size,
                'dead': 0
            },
            'organisms': species_organism_list
        }

    return population_dict


def load_species_from_param_files(fns,
                                  init_world,
                                  custom_module_fns=None,
                                  seed=None):
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
    custom_module_fns : list of str
        List of external Python scripts containing custom organism
        behaviors. :mod:`blossom` will search for methods within each
        filename included here.
    seed : int, Generator, optional
        Random seed for the simulation

    Returns
    -------
    population_dict : dict of Organisms
        A dict of Organism objects constructed from the parameter file.

    """
    # Find organism filenames, can be a list of patterns
    fns = cast_to_list(fns)
    org_files = [fn for pattern in fns for fn in glob.glob(pattern)]

    # Initialize list of dictionaries to hold all organism parameters
    # Each dictionary contains parameters for a single species
    population_dict = {}
    for i, org_file in enumerate(org_files):
        # Initialize temporary dict to store species parameters
        species_init_dict = {}

        # Parameters that must be str or None
        param_str = ['species_name',
                     'action_type',
                     'movement_type',
                     'reproduction_type',
                     'drinking_type',
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
        # converting them to proper types as specified above
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
        species_init_dict['custom_module_fns'] = custom_module_fns

        species_organism_list = create_organisms(species_init_dict, init_world, seed=seed)

        # Populate population dict with relevant bulk stats and organism lists
        population_dict[species_init_dict['species_name']] = {
            'statistics': {
                'total': species_init_dict['population_size'],
                'alive': species_init_dict['population_size'],
                'dead': 0
            },
            'organisms': species_organism_list
        }

    return population_dict


def parse_config_number(x):
    """
    If config number is the string 'inf', use ``np.inf``.
    """
    if x == 'inf':
        x = np.inf 
    return x


def load_from_config(fn, seed=None):
    """
    Create initial population and world from .yml configuration file.
    """
    with open(fn, 'r') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    initial_seed = cfg.get('seed', seed)
    if initial_seed is None:
        initial_seed = np.random.default_rng().integers(2**32)
    rng = np.random.default_rng(initial_seed)    
    config_params = {
        'initial_seed': initial_seed,
        'rng': rng
    }
    
    # Load world
    world_cfg = cfg['world']
    size = world_cfg['size']

    world_init_dict = {'world_size': size}
    if 'water' in world_cfg:
        peak = world_cfg['water']['peak']
        world_init_dict['water'] = np.full(size, parse_config_number(peak))
    else:
        world_init_dict['water'] = np.full(size, np.inf)
    if 'food' in world_cfg:
        peak = world_cfg['food']['peak']
        if peak == 'inf':
            peak = np.inf
        world_init_dict['food'] = np.full(size, peak)
    else:
        world_init_dict['food'] = np.full(size, np.inf)
    if 'obstacles' in world_cfg:
        peak = world_cfg['obstacles']['peak']
        if peak == 'inf':
            peak = np.inf
        world_init_dict['obstacles'] = np.full(size, peak)
    else:
        world_init_dict['obstacles'] = np.full(size, 0)
    world = load_world_from_dict(world_init_dict)

    # Load species
    species_cfgs = cfg['species']
    species_init_dicts=[]
    for species_cfg in species_cfgs:
        species_init_dict = {
            'population_size': species_cfg['population'],
            'species_name': species_cfg['name'],
            'max_age': parse_config_number(species_cfg['max_age']),
            'custom_module_fns': species_cfg['linked_modules']
        }
        # Action
        action = species_cfg['action']
        if isinstance(action, str):
            species_init_dict['action_type'] = action 
        elif isinstance(action, dict):
            species_init_dict['action_type'] = action['type']

        # Movement 
        movement = species_cfg.get('movement')
        if isinstance(movement, str):
            species_init_dict['movement_type'] = movement 
        elif isinstance(movement, dict):
            species_init_dict['movement_type'] = movement['type']

        # Reproduction 
        reproduction = species_cfg.get('reproduction')
        if isinstance(reproduction, str):
            species_init_dict['reproduction_type'] = reproduction 
        elif isinstance(reproduction, dict):
            species_init_dict['reproduction_type'] = reproduction['type']

        # Drinking 
        drinking = species_cfg.get('drinking')
        if drinking is not None:
            species_init_dict.update({
                'drinking_type': drinking['type'],
                'water_capacity': drinking['capacity'],
                'water_initial': drinking['initial'],
                'water_metabolism': drinking['metabolism'],
                'water_intake': drinking['intake'],
                'max_time_without_water': drinking['days_without']
            })

        # Eating 
        eating = species_cfg.get('eating')
        if eating is not None:
            species_init_dict.update({
                'eating_type': eating['type'],
                'food_capacity': eating['capacity'],
                'food_initial': eating['initial'],
                'food_metabolism': eating['metabolism'],
                'food_intake': eating['intake'],
                'max_time_without_food': eating['days_without']
            })

        species_init_dicts.append(species_init_dict)

    population_dict = load_species_from_dict(species_init_dicts,
                                             world,
                                             seed=rng)

    return population_dict, world, config_params

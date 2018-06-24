import os
import glob
import configparser
import json
import numpy as np
import random

import fields
from world import World
from organism import Organism


class DatasetIO():
    """
    Load information from a certain dataset, e.g. to resume a simulation, and
    write world and organism data back to file.
    """

    # returns list of dictionaries
    # class method:
    # @classmethod
    def load_world_dataset(fn):
        """
        Load dataset file from JSON.
        filenames can be a single string or a list of strings.

        Args:
            fn (str): Input filename of saved world dataset
            field_names (list): World attributes to load from file

        Returns:
            World: The return value. The reconstructed World object
            from the saved dataset.
        """
        with open(fn, 'r') as f:
            world_dict = json.load(f)
        return World(world_dict)

    def write_world_dataset(world, fn):
        """
        Write world information from World object to file in JSON format.

        Args:
            fn (str): Output filename of saved world dataset
            field_names (list): World attributes to write to file
        """
        with open(fn, 'w') as f:
            json.dump(vars(world), f, indent=2)

    # returns list of dictionaries
    # class method:
    # @classmethod
    def load_organism_dataset(fn):
        """
        Load dataset file from JSON.
        filenames can be a single string or a list of strings.

        Args:
            fn (str): Input filename of saved organism dataset
            field_names (list): Organism attributes to load (per organism)
                from file

        Returns:
            list: The return value. A list of Organism objects
            reconstructed from the saved dataset.
        """
        with open(fn, 'r') as f:
            organism_dict_list = json.load(f)
        organism_list = [Organism(organism_dict) for organism_dict in organism_dict_list]
        return organism_list

    def write_organism_dataset(organism_list, fn):
        """
        Write organism data from list of Organism objects to file in JSON
        format.

        Args:
            fn (str): Output filename of saved organism dataset
            field_names (list): Organism attributes to write (per organism)
                to file.
        """
        organism_dict_list = [vars(organism) for organism in organism_list]
        with open(fn, 'w') as f:
            json.dump(organism_dict_list, f, indent=2)

class ParameterIO():
    """
    Load initial parameters from parameter files.
    """

    # class method:
    # @classmethod
    def load_world_parameters(fn):
        """
        Load world parameter files.
        filenames can be a single string or a list of strings.

        Args:
            fn (str): Input filename of parameter file

        Returns:
            World: The return value. A World object constructed
            from the parameter file.
        """

        env_file = glob.glob(fn)
        if len(env_file) == 0:
            raise IndexError('There is no environment configuration file in the '
                + 'current directory.')
        if len(env_file) > 1:
            print('There are multiple environment configuration files in the current '
                + 'directory. There should only be one environment configuration file. '
                + 'Selecting one at random.')
        env_file = env_file[0]

        world_dict = {}
        # Load from config file
        config_world = configparser.ConfigParser()
        config_world.read(env_file)

        # dimensionality: int
        dimensionality = int(config_world.get('Overall Parameters', 'dimensionality'))
        world_dict['dimensionality'] = dimensionality

        # world_size: space delimited ints in agreement with dimensionality, or 'None'
        # example: world_size = 10 10
        world_size = config_world.get('Overall Parameters', 'world_size')
        if world_size == 'None':
            # this is probably harder to do, since we'd have to allow for infinite bounds...
            world_size = None
        else:
            world_size = [int(L) for L in world_size.split()]
        world_dict['world_size'] = world_size

        # environment_filename: str, or 'None'
        environment_filename = config_world.get('Overall Parameters',
                                                'environment_filename')
        if environment_filename == 'None':
            environment_filename = None
        world_dict['environment_filename'] = environment_filename

        return World(world_dict)


    # class method:
    # @classmethod
    def load_species_parameters(fns, init_world):
        """
        Load all available species parameter files.
        filenames can be a single string or a list of strings.

        Args:
            fn (str): Input filename of parameter file

        Returns:
            list: The return value. A list of Organism objects constructed
            from the parameter file.
        """

        # Find organism filenames, can be a list of patterns
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
                for (key,val) in config_org.items(section):

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

            # Generate all organisms
            for i in range(organism_dict['population_size']):
                # Vary organism location randomly
                position = []
                for i in range(init_world.dimensionality):
                    position.append(random.randrange(0,init_world.world_size[i]))
                organism_dict['position'] = position

                # Add organism to organism list
                organism_list.append(Organism(organism_dict))

            return organism_list

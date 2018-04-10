import csv
import configparser
import os, glob

class DatasetStorage(object):
    """
    Store information from a certain dataset, e.g. to resume a simulation.
    """

    def __init__(self, world_fn='', organism_fns=[]):
        self.world_fn = world_fn
        self.organism_fns = organism_fns
        self.world_records = self.read_datasets(world_fn)
        self.organism_records = self.read_datasets(organism_fns)

    def read_datasets(fns):
        """
        Load dataset files.
        filenames can be a single string or a list of strings.
        """
        vals = []
        for fn in fns:
            f = open(fn, 'r')
            reader = csv.DictReader(f, field_names)
            for row in reader:
                vals.append(row)
            f.close()
        return vals


class ParameterStorage(object):
    """
    Store initial parameters from parameter files.
    """
    def __init__(self, world_fn='', species_fs=[]):
        self.world_fn = world_fn
        self.species_fns = species_fns
        self.world_records = self.read_world_params(world)
        self.species_records = self.read_species_params(species)

    def read_world_params(fns):
        """
        Load world parameter files.
        filenames can be a single string or a list of strings.
        """

        env_file = glob.glob(fns)
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


    def read_species_params(fns):
        """
        Load all available species parameter files.
        filenames can be a single string or a list of strings.
        """

        # Find organism filenames
        org_files = glob.glob('*.org')

        # Initialize list of dictionaries to hold all organism parameters
        # Each dictionary contains parameters for a single species
        org_dict_list = []
        for org_file in org_files:
            # Initialize temporary dict to store species parameters
            org_dict = {}

            # Parameters that must be str
            param_str = ['species_name',
                         'movement_type',
                         'food_intake_prescription',
                         'reproduction_type']

            # Parameters that must be int
            param_int = ['population_size',
                         'dna_length']

            # Parameters that must be int or 'None'
            param_int_none = ['max_age',
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
                    elif key in param_bool:
                        val = (val == 'True')
                    else:
                        raise NameError('Key is not a valid parameter')
                    # ensure 'None' parameters are set to None
                    if val == 'None':
                        val = None
                    org_dict[key] = val

            org_dict_list.append(org_dict)

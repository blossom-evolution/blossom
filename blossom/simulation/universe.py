import click 
import os
import yaml
from pathlib import Path

import time
import numpy as np

from . import parse_intent
from . import utils
from . import dataset_io as dio
from . import parameter_io as pio
from . import population_funcs as pf


class Universe(object):
    """
    Create the universe of the simulation.
    """

    def __init__(self,
                 dataset_fn=None,
                 config_fn=None,
                 world_param_fn=None,
                 species_param_fns=None,
                 world_param_dict={},
                 species_param_dicts=[{}],
                 custom_module_fns=None,
                 current_time=0,
                 end_time=1000,
                 run_dir='datasets/',
                 pad_zeros=4,
                 seed=None):
        """
        Initialize universe based on either parameter files or saved datasets.

        Parameters
        ----------
        dataset_fn : str
            Filename of saved organism and world datasets
        config_fn : str 
            Filename of config .yml file
        world_param_fn : str
            Filename of world parameter file
        species_param_fns : list of str
            List of filenames of species parameter files
        world_param_dict : dict
            Dictionary containing initial world parameters
        species_param_dicts : list of dict
            List of dictionaries containing initial species parameters
        custom_module_fns : list of str
            List of filenames of external python scripts containing custom
            behaviors
        current_time : int
            Current time of simulation
        end_time : int
            End time of simulation
        run_dir : str
            Directory path for saving all run files
        pad_zeros : int
            Number of zeroes to pad in dataset filenames
        seed : int, Generator, optional
            Random seed for the simulation
        """
        # Set random seeds for the entire simulation
        self.rng = np.random.default_rng(seed)

        self.start_timestamp = time.time()
        self.last_timestamp = self.start_timestamp
        self.elapsed_time = 0

        input_count = 0
        self.dataset_fn = dataset_fn
        if self.dataset_fn is not None:
            input_count += 1

        self.config_fn = config_fn
        if self.config_fn is not None:
            input_count += 1

        self.world_param_fn = world_param_fn
        self.species_param_fns = species_param_fns
        if self.world_param_fn is not None and self.species_param_fns is not None:
            input_count += 1
            
        self.world_param_dict = world_param_dict
        self.species_param_dicts = species_param_dicts
        if self.world_param_dict != {} and self.species_param_dicts != [{}]:
            input_count += 1

        if input_count == 0:
            raise ValueError('No valid initialization provided')
        elif input_count > 1:
            raise ValueError('Only one initialization method may be provided')

        self.custom_module_fns = custom_module_fns
        if self.custom_module_fns is not None:
            self.custom_module_fns = [os.path.abspath(path)
                                      for path in self.custom_module_fns
                                      if os.path.isfile(path)]

        self.run_dir = Path(run_dir).resolve()
        self.run_dir.mkdir(exist_ok=True)
        (self.run_dir / 'data').mkdir(exist_ok=True)
        (self.run_dir / 'logs').mkdir(exist_ok=True)

        self.current_time = current_time
        self.end_time = end_time
        self.pad_zeros = pad_zeros

        self.initialize(seed=seed)
        self.organisms = pf.get_organism_list(self.population_dict)
        self.organisms_by_location = pf.hash_by_location(self.organisms)
        self.species_names = sorted(list(self.population_dict.keys()))
        self.intent_list = []

    def initialize(self, seed=None):
        """
        Initialize world and organisms in the universe, from either saved
        datasets or from parameter files (and subsequently writing the
        initial time step to file).

        Returns
        -------
        population_dict : dict
            Dict of organisms at the beginning of the simulation.
        world : World
            World at the beginning of the simulation.
        """
        if self.dataset_fn is not None:
            # Set up entire universe based on saved dataset
            self.population_dict, self.world, self.rng = dio.load_universe(self.dataset_fn, 
                                                                           seed=seed)
            self.current_time = self.world.current_time
        else:
            if self.config_fn is not None:
                self.population_dict, self.world, self.rng = pio.load_from_config(self.config_fn,
                                                                                seed=seed)
            elif self.world_param_fn is not None and self.species_param_fns is not None:
                self.world = pio.load_world_from_param_file(self.world_param_fn)
                self.population_dict = pio.load_species_from_param_files(
                                    fns=self.species_param_fns,
                                    init_world=self.world,
                                    custom_module_fns=self.custom_module_fns,
                                    seed=self.rng)
            elif self.world_param_fn != {} and self.species_param_fns != [{}]:
                self.world = pio.load_world_from_dict(self.world_param_dict)
                self.population_dict = pio.load_species_from_dict(
                                    init_dicts=self.species_param_dicts,
                                    init_world=self.world,
                                    custom_module_fns=self.custom_module_fns,
                                    seed=self.rng)
            else:
                raise ValueError('No valid intialization provided')
        
            dio.save_universe(self)

    def step(self):
        """
        Steps through one time step, iterating over all organisms and
        computing new organism states. Saves all organisms and the world
        to file at the end of each step.
        """
        # Increment time step
        self.current_time += 1

        # This is just updating the age, not evaluating whether an organism
        # is at death, since organism actions should be evaluated based on
        # the current state. Age needs to be updated so that every organism
        # in intent list has the correct age.
        last_organisms = self.organisms
        self.organisms = [organism.clone_self()._update_age()
                          for organism in last_organisms
                          if organism.alive]
        self.population_dict = pf.get_population_dict(self.organisms,
                                                      self.species_names)
        self.organisms_by_location = pf.hash_by_location(self.organisms)

        # intent_list is a list of lists, one list per organism in the current
        # time step
        self.intent_list = []
        for organism in last_organisms:
            if organism.alive:
                # Use updated organism ages, and pass Universe to organism step
                self.intent_list.append(organism.step(self))

        # Parse intent list and ensure it is valid
        self.organisms = parse_intent.parse(self.intent_list, last_organisms)
        self.population_dict = pf.get_population_dict(self.organisms,
                                                      self.species_names)
        self.organisms_by_location = pf.hash_by_location(self.organisms)

        # Potential changes to the world would go here
        self.world.step()

        # Save universe state
        now = time.time()
        self.elapsed_time = now - self.last_timestamp
        self.last_timestamp = now
        dio.save_universe(self)

    def current_info(self, verbosity=1, expanded=True):
        total_num = sum([self.population_dict[species]['statistics']['total']
                         for species in self.species_names])

        pstring = 't = %s' % (self.current_time)
        if verbosity >= 1:
            if expanded:
                pstring = (
                    '... t = %s\n'
                    % str(self.current_time).zfill(self.pad_zeros)

                    + '    Number of organisms: %s\n'
                      % total_num
                )
            else:
                rt_pstring = 't = %s: %s organisms' % (self.current_time,
                                                       total_num)
        if verbosity >= 4:
            if expanded:
                for species_name in self.species_names:
                    pstring += (
                        '    %s: %d organisms\n'
                        % (species_name, self.population_dict[species_name]['statistics']['total'])
                    )
            else:
                rt_pstring = rt_pstring + ' ('
                for i, species_name in enumerate(self.species_names):
                    rt_pstring += str(self.population_dict[species_name]['statistics']['total'])
                    if i != len(self.species_names) - 1:
                        rt_pstring += ':'
                rt_pstring += ')'

        if verbosity >= 2:
            if expanded:
                pstring += (
                    '    Time elapsed since last time step: %s\n'
                    % utils.time_to_string(self.elapsed_time)
                )
            else:
                pstring = rt_pstring + (
                    ' (%s)'
                    % (utils.time_to_string(self.elapsed_time))
                )
        if verbosity >= 3:
            start_time_diff = time.time() - self.start_timestamp
            if expanded:
                pstring += (
                    '    Time elapsed since start: %s\n'
                    % utils.time_to_string(start_time_diff)
                )
            else:
                pstring = rt_pstring + (
                    ' (%s; %s)'
                    % (utils.time_to_string(self.elapsed_time),
                       utils.time_to_string(start_time_diff))
                )

        return pstring

    def run(self, verbosity=1, expanded=True):
        print(self.current_info(verbosity=verbosity, expanded=expanded))
        while self.current_time < self.end_time:
            self.step()
            print(self.current_info(verbosity=verbosity, expanded=expanded))


@click.command(name='run')
@click.option('-t', '--timesteps', default=1000,
              help='Max timestep for run')
@click.option('-r', '--restart', is_flag=True, default=False,
              help='Option to erase past data files before run')
@click.option('-v', '--verbosity', default=4,
              help='Level of progress detail to print')
@click.option('-s', '--seed', type=int,
              help='Random seed')
def run_universe(timesteps, restart=False, verbosity=4, seed=None):
    run_path = Path('.').resolve()

    logs_path = run_path / 'logs'
    data_path = run_path / 'data'

    if data_path.is_dir():
        data_fns = sorted(data_path.glob('*.json'))
        if len(data_fns) > 0 and not restart:
            universe = Universe(dataset_fn=data_fns[-1], 
                                run_dir=run_path,
                                end_time=timesteps, 
                                seed=seed)
            universe.run(verbosity=verbosity, expanded=False)
            return

    if restart:
        if logs_path.is_dir():
            for fn in logs_path.iterdir():
                fn.unlink()
        if data_path.is_dir():
            for fn in data_path.iterdir():
                fn.unlink()

    # Run even if not restarting, such as first run
    # Use .yml 
    config_path = list(run_path.glob('*.yml'))
    if len(config_path) == 1:
        config_path = config_path[0]
        with open(config_path, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        timesteps = cfg.get('timesteps', timesteps)

        universe = Universe(config_fn=config_path, 
                            run_dir=run_path,
                            end_time=timesteps, 
                            seed=seed)
        universe.run(verbosity=verbosity, expanded=False)
        return
    elif len(config_path) == 0:
        raise ValueError('No config files')
    else:
        raise ValueError('Multiple config files located')


# At its simplest, the entire executable could just be written like this
if __name__ == '__main__':
    universe = Universe()
    universe.run()

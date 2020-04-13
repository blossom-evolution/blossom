import sys
import os
import errno
from collections import Counter

import time

import parse_intent
import utils
import dataset_io as dio
import parameter_io as pio
import organism_list_funcs


class Universe(object):
    """
    Create the universe of the simulation.
    """

    def __init__(self,
                 world_ds_fn=None,
                 organisms_ds_fn=None,
                 world_param_fn=None,
                 species_param_fns=None,
                 world_param_dict={},
                 species_param_dicts=[{}],
                 custom_module_fns=None,
                 current_time=0,
                 end_time=10,
                 dataset_dir='datasets/',
                 pad_zeroes=0,
                 file_extension='.txt'):
        """
        Initialize universe based on either parameter files or saved datasets.

        Parameters
        ----------
        world_ds_fn : str
            Filename of saved world dataset.
        organisms_ds_fn : str
            Filename of saved organism dataset.
        world_param_fn : str
            Filename of world parameter file.
        species_param_fns : list of str
            List of filenames of species parameter files.
        world_param_dict : dict
            Dictionary containing initial world parameters.
        species_param_dicts : list of dict
            List of dictionaries containing initial species parameters.
        custom_module_fns : list of str
            List of filenames of external python scripts containing custom
            behaviors.
        current_time : int
            Current time of simulation.
        end_time : int
            End time of simulation.
        dataset_dir : str
            Directory path for saving all world and organism datasets.
        pad_zeroes : int
            Number of zeroes to pad in dataset filenames.
        file_extension : str
            File extension for saving dataset files. Should generally be '.txt'
            or '.json'.

        """
        self.start_timestamp = time.time()
        self.last_timestamp = self.start_timestamp

        self.world_ds_fn = world_ds_fn
        self.organisms_ds_fn = organisms_ds_fn
        self.world_param_fn = world_param_fn
        self.species_param_fns = species_param_fns
        self.custom_module_fns = custom_module_fns

        self.world_param_dict = world_param_dict
        self.species_param_dicts = species_param_dicts

        if self.custom_module_fns is not None:
            self.custom_module_fns = [os.path.abspath(path)
                                      for path in self.custom_module_fns
                                      if os.path.isfile(path)]

        self.dataset_dir = dataset_dir
        if dataset_dir[-1] != '/':
            self.dataset_dir += '/'
        try:
            os.makedirs(dataset_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        self.current_time = current_time
        self.end_time = end_time
        self.pad_zeroes = pad_zeroes
        while (self.end_time - self.current_time) >= 10 ** self.pad_zeroes:
            self.pad_zeroes += 1
        self.file_extension = file_extension

        # world is a World object
        self.world = self.initialize_world()
        # organisms is a list of Organism objects
        self.organism_list = self.initialize_organisms()

        self.species_names = set(organism.species_name
                                 for organism in self.organism_list)
        self.species_names = sorted(list(self.species_names))
        self.intent_list = []

    def initialize_world(self):
        """
        Initialize the world of the universe from either a saved dataset
        or from a parameter file (and subsequently writing the
        initial time step to file).

        Returns
        -------
        world : World
            World at the beginning of the simulation.
        """
        if self.world_ds_fn is not None:
            # Set up entire world based on world records
            world = dio.load_world(self.world_ds_fn)
        else:
            if self.world_param_fn is not None:
                # Set up entire world based on parameter file
                world = pio.load_world(fn=self.world_param_fn)
            else:
                world = pio.load_world(init_dict=self.world_param_dict)
            output_fn = (self.dataset_dir + 'world_ds'
                         + str(self.current_time).zfill(self.pad_zeroes)
                         + self.file_extension)
            dio.save_world(world, output_fn)
        return world

    def initialize_organisms(self):
        """
        Initialize all organisms in the universe from either a saved dataset
        or from parameter files (and subsequently writing the
        initial time step to file).

        Returns
        -------
        organism_list : list of Organisms
            List of organisms at the beginning of the simulation.
        """
        if self.organisms_ds_fn is not None:
            # Set up all organisms based on organism records
            organism_list = dio.load_organisms(self.organisms_ds_fn)
        else:
            if self.species_param_fns is not None:
                # Set up all organisms based on species specifications
                organism_list = pio.load_species(
                                    fns=self.species_param_fns,
                                    init_world=self.world,
                                    custom_module_fns=self.custom_module_fns)
            else:
                organism_list = pio.load_species(
                                    init_dicts=self.species_param_dicts,
                                    init_world=self.world,
                                    custom_module_fns=self.custom_module_fns)
            output_fn = (self.dataset_dir + 'organisms_ds'
                         + str(self.current_time).zfill(self.pad_zeroes)
                         + self.file_extension)
            dio.save_organisms(organism_list, output_fn)
        return organism_list

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
        t_organism_list = [organism.clone_self()._update_age()
                           for organism in self.organism_list
                           if organism.alive]
        position_hash_table = (organism_list_funcs
                               .hash_by_position(t_organism_list))

        # intent_list is a list of lists, one list per organism in the current
        # time step
        self.intent_list = []
        for organism in self.organism_list:
            if organism.alive:
                # currently t_organism_list isn't used by any actions...
                self.intent_list.append(
                    organism.step(t_organism_list,
                                  self.world,
                                  position_hash_table=position_hash_table)
                )

        # Parse intent list and ensure it is valid
        # Decide whether this should be self.organism_list or organism_list
        self.organism_list = parse_intent.parse(self.intent_list,
                                                self.organism_list)

        org_output_fn = (self.dataset_dir + 'organisms_ds'
                         + str(self.current_time).zfill(self.pad_zeroes)
                         + self.file_extension)
        dio.save_organisms(self.organism_list, org_output_fn)

        world_output_fn = (self.dataset_dir + 'world_ds'
                           + str(self.current_time).zfill(self.pad_zeroes)
                           + self.file_extension)
        # Potential changes to the world would go here
        dio.save_world(self.world, world_output_fn)

    def current_info(self, verbosity=1, expanded=True):
        pstring = 't = %s' % (self.current_time)
        if verbosity >= 1:
            if expanded:
                pstring = (
                    '... t = %s\n'
                    % str(self.current_time).zfill(self.pad_zeroes)

                    + '    Number of organisms: %s\n'
                      % len(self.organism_list)
                )
            else:
                rt_pstring = 't = %s: %s organisms' % (self.current_time,
                                                       len(self.organism_list))
        if verbosity >= 4:
            counter = Counter([org.species_name for org in self.organism_list])
            if expanded:
                for species_name in self.species_names:
                    pstring += (
                        '    %s: %d organisms\n'
                        % (species_name, counter[species_name])
                    )
            else:
                rt_pstring = rt_pstring + ' ('
                for i, species_name in enumerate(self.species_names):
                    rt_pstring += str(counter[species_name])
                    if i != len(self.species_names) - 1:
                        rt_pstring += ':'
                rt_pstring += ')'

        if verbosity >= 2:
            now = time.time()
            last_time_diff = now - self.last_timestamp
            self.last_timestamp = now
            if expanded:
                pstring += (
                    '    Time elapsed since last time step: %s\n'
                    % utils.time_to_string(last_time_diff)
                )
            else:
                pstring = rt_pstring + (
                    ' (%s)'
                    % (utils.time_to_string(last_time_diff))
                )
        if verbosity >= 3:
            start_time_diff = now - self.start_timestamp
            if expanded:
                pstring += (
                    '    Time elapsed since start: %s\n'
                    % utils.time_to_string(start_time_diff)
                )
            else:
                pstring = rt_pstring + (
                    ' (%s; %s)'
                    % (utils.time_to_string(last_time_diff),
                       utils.time_to_string(start_time_diff))
                )

        return pstring

    def run(self, verbosity=1, expanded=True):
        print(self.current_info(verbosity=verbosity, expanded=expanded))
        while self.current_time < self.end_time:
            self.step()
            print(self.current_info(verbosity=verbosity, expanded=expanded))


# At its simplest, the entire executable could just be written like this
if __name__ == '__main__':
    universe = Universe()
    universe.run()

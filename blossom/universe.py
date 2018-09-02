import sys
import os
import glob
import errno
import numpy as np

import parse_intent
from data_io import DatasetIO as DIO
from data_io import ParameterIO as PIO

class Universe(object):
    """
    Create the universe of the simulation.
    """

    def __init__(self,
                 world_fn=None,
                 organism_fns=None,
                 world_param_fn=None,
                 species_param_fns=None,
                 current_time=0,
                 end_time=10,
                 dataset_dir='datasets/',
                 pad_zeroes=4,
                 file_extension='.txt'):
        self.world_param_fn = world_param_fn
        self.species_param_fns = species_param_fns
        self.world_fn = world_fn
        self.organism_fns = organism_fns

        self.current_time = current_time
        self.end_time = end_time

        self.dataset_dir = dataset_dir
        if dataset_dir[-1] != '/':
            self.dataset_dir += '/'
        try:
            os.makedirs(dataset_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        self.pad_zeroes = pad_zeroes
        while (self.end_time - self.current_time) >= 10**self.pad_zeroes:
            self.pad_zeroes += 1
        self.file_extension = file_extension

        # world is a World object
        self.world = self.initialize_world()
        # organisms is a list of Organism objects
        self.organism_list = self.initialize_organisms()
        self.intent_list = []

    # return World object
    def initialize_world(self):
        # world = world.World()
        if self.world_fn is not None:
            # Set up entire world based on world records
            world = DIO.load_world_dataset(self.world_fn)
        elif self.world_param_fn is not None:
            # Set up entire world based on parameter file
            world = PIO.load_world_parameters(self.world_param_fn)
            DIO.write_world_dataset(world, self.dataset_dir + 'world_ds' + str(self.current_time).zfill(self.pad_zeroes) + self.file_extension)
        else:
            sys.exit('No files specified for initialization!')
        return world

    def initialize_organisms(self):
        # organisms is a list of Organism objects
        # organisms = []
        if self.organism_fns is not None:
            # Set up all organisms based on organism records
            organism_list = DIO.load_organism_dataset(self.organism_fns)
        elif self.species_param_fns is not None:
            # Set up all organisms based on species specifications
            organism_list = PIO.load_species_parameters(self.species_param_fns, self.world)
            DIO.write_organism_dataset(organism_list, self.dataset_dir + 'organisms_ds' + str(self.current_time).zfill(self.pad_zeroes) + self.file_extension)
        else:
            sys.exit('No files specified for initialization!')
        return organism_list

    def step(self):
        self.intent_list = []
        for organism in self.organism_list:
            for new_organism in organism.step(self.organism_list, self.world):
                self.intent_list.append(new_organism)

        self.current_time += 1
        # Parse intent list and ensure it is valid
        self.organism_list = parse_intent.parse(self.intent_list, self.organism_list)
        DIO.write_organism_dataset(self.organism_list, self.dataset_dir + 'organisms_ds' + str(self.current_time).zfill(self.pad_zeroes) + self.file_extension)

        # self.world = None
        DIO.write_world_dataset(self.world, self.dataset_dir + 'world_ds' + str(self.current_time).zfill(self.pad_zeroes) + self.file_extension)


# the entire executable could just be written like this
# and everything happens under the hood
# well, we have to include parameter input options,
# but these can go straight into Universe initialization
if __name__ == '__main__':
    universe = Universe()
    while universe.current_time < universe.end_time:
        universe.step()

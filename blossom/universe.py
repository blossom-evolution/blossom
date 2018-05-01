import parameter_file_storage.DatasetLoad as dl
import parameter_file_storage.ParameterLoad as pl
import fields
import sys
import os
import glob
import world
import species
import organism

class Universe(object):
    """
    Create the universe of the simulation.
    """

    def __init__(self,
                 world_fn='',
                 organism_fns=[],
                 world_param_fn='',
                 species_param_fs=[],
                 current_time=0,
                 end_time=10):
        self.world_param_fn = world_param_fn
        self.species_param_fns = species_param_fns
        self.world_fn = world_fn
        self.organism_fns = organism_fns
        self.current_time = current_time
        self.end_time = end_time

        # world is a World object
        self.world = initialize_world(world_fns, world_param_fn)
        # organisms is a list of Organism objects
        self.organisms = initialize_organisms(organism_fns, species_param_fs)
        pass

    # return World object
    def initialize_world(self, world_fns='', world_param_fn=''):
        # organism_records is a list of dictionaries
        # world = world.World()
        if len(world_fns) > 0:
            world_records = dl.load_datasets(world_fns,
                                                fields.world_field_names.keys())
            # TODO: set up entire world based on world records
        elif len(world_param_fs) > 0:
            world_params = pl.load_world_params(world_param_fn)
            # TODO: set up entire world based on parameter file
            pass
        else:
            sys.exit('No files specified for initialization!')
        return world

    def initialize_organisms(self, organism_fns=[], species_param_fs=[]):
        # organisms is a list of Organism objects
        # organisms = []
        if len(organism_fns) > 0:
            organism_records = dl.load_datasets(organism_fns,
                                                fields.organism_field_names.keys())
            # TODO: set up all organisms based on organism records
        elif len(species_param_fs) > 0:
            species_params = pl.load_species_params(species_param_fns)
            # TODO: set up all organisms based on species specifications
            pass
        else:
            sys.exit('No files specified for initialization!')
        return organisms

    def step(self):
        pass

# the entire executable could just be written like this
# and everything happens under the hood
# well, we have to include parameter input options,
# but these can go straight into Universe initialization
universe = Universe()
while universe.current_time < universe.end_time:
    universe.step()

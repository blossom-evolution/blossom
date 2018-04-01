import blossom
import glob
import numpy as np

# PSEUDOCODE
simulation_param_filename = load(simulations_param_filename)
get_relevant_parameters()

world_filename = load(world_parameter_filename)
World world = blossom.load_world(world_filename)

species_filenames = load(species_parameter_files)
species_list = []
# figure out better way to get organism locations
organism_locations_list = []
for species_filename in glob(species_filenames):
    Species species, organism_locations = blossom.load_species(species_filename)
    species_list.append(species)
    organism_locations_list.append(organism_locations)

organism_list = []
for index in range(len(species)):
    species = species_list[index]
    for location in organism_locations_list[index]:
    Organism organism = blossom.organism_init(species, location)
    organism_list.append(organism)

Universe universe = universe_init(world, species_list, organism_list,
                                  current_time, end_time, timestep)
while(universe.current_time<universe.end_time)
    # so.. a whole lot of (nontrivial) implementation should go into this, lol
    universe.step()

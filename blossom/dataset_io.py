"""
Load information from a certain dataset, e.g. to resume a simulation, and
write world and organism data back to file.
"""

import json

from world import World
from organism import Organism

def load_world_dataset(fn):
    """
    Load dataset file from JSON.
    filenames can be a single string or a list of strings.

    Parameters
    ----------
    fn : str
        Input filename of saved world dataset.

    Returns
    -------
    world : World
        World object reconstructed from the saved dataset.
    """
    with open(fn, 'r') as f:
        world_dict = json.load(f)
    return World(world_dict)

def write_world_dataset(world, fn):
    """
    Write world information from World object to file in JSON format.

    Parameters
    ----------
    world : World
        World attributes to write to file.
    fn : str
        Output filename of saved world dataset.
    """
    with open(fn, 'w') as f:
        json.dump(vars(world), f, indent=2)

def load_organism_dataset(fn):
    """
    Load dataset file from JSON.
    filenames can be a single string or a list of strings.

    Parameters
    ----------
    fn : str
        Input filename of saved organism dataset.

    Returns
    -------
    organism_list : list of Organisms
        A list of Organism objects reconstructed from the saved dataset.
    """
    with open(fn, 'r') as f:
        organism_dict_list = json.load(f)
    organism_list = [Organism(organism_dict) for organism_dict in organism_dict_list]
    return organism_list

def write_organism_dataset(organism_list, fn):
    """
    Write organism data from list of Organism objects to file in JSON
    format.

    Parameters
    ----------
    organism_list : list of Organisms
        List of Organisms to write to file.
    fn : str
        Output filename of saved organism dataset.
    """
    organism_dict_list = []
    for organism in organism_list:
        organism_dict = vars(organism)
        # Make sure we're not serializing the loaded modules themselves
        del organism_dict['custom_modules']
        organism_dict_list.append(organism_dict)
    with open(fn, 'w') as f:
        json.dump(organism_dict_list, f, indent=2)

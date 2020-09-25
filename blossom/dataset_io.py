"""
Load information from a certain dataset, e.g. to resume a simulation, and
write world and organism data back to file.
"""

import copy
import json

from world import World
from organism import Organism
import population_funcs


def load_world(fn):
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


def save_world(world, fn):
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
        json.dump(world.to_dict(), f, indent=2)


def load_organisms(fn):
    """
    Load dataset file from JSON.
    filenames can be a single string or a list of strings.

    Parameters
    ----------
    fn : str
        Input filename of saved organism dataset.

    Returns
    -------
    population_dict : dict
        A dict of Organism objects reconstructed from the saved dataset.
    """
    with open(fn, 'r') as f:
        population_dict_json = json.load(f)

    population_dict = {}
    for species in population_dict_json:
        population_dict[species] = {}
        population_dict[species]['statistics'] = copy.deepcopy(population_dict_json[species]['statistics'])
        population_dict[species]['organisms'] = [
            Organism(organism_dict)
            for organism_dict in population_dict_json[species]['organisms']
        ]
    return population_dict


def save_organisms(population_dict, fn):
    """
    Write organism data from dict of Organism objects to file in JSON
    format.

    Parameters
    ----------
    population_dict : dict
        Dict of Organisms to write to file.
    fn : str
        Output filename of saved organism dataset.
    """
    population_dict_json = {}
    for species in population_dict:
        population_dict_json[species] = {}
        population_dict_json[species]['statistics'] = copy.deepcopy(population_dict[species]['statistics'])
        population_dict_json[species]['organisms'] = [
            organism.to_dict()
            for organism in population_dict[species]['organisms']
        ]

    with open(fn, 'w') as f:
        json.dump(population_dict_json, f, indent=2)

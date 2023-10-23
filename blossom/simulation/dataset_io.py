"""
Load information from a certain dataset, e.g. to resume a simulation, and
write world and organism data back to file.
"""

import copy
import json
from pathlib import Path

from .world import World
from .organism import Organism


def load_universe(fn):
    """
    Load dataset file from JSON.

    Parameters
    ----------
    fn : str
        Input filename of saved universe dataset.

    Returns
    -------
    population_dict : dict
        A dict of Organism objects reconstructed from the saved dataset.
    world : World
        World object reconstructed from the saved dataset.
    """
    with open(fn, 'r') as f:
        universe_dict = json.load(f)

    world = World(universe_dict['world'])

    population_dict_json = universe_dict['population']
    population_dict = {}
    for species in population_dict_json:
        population_dict[species] = {}
        population_dict[species]['statistics'] = population_dict_json[species]['statistics']
        population_dict[species]['organisms'] = [
            Organism(organism_dict)
            for organism_dict in population_dict_json[species]['organisms']
        ]

    return population_dict, world


def save_universe(population_dict, world, fn):
    """
    Save population_dict and world to file in JSON format.

    Parameters
    ----------
    population_dict : dict
        Dict of Organisms to write to file.
    world : World
        World attributes to write to file.
    fn : str
        Output filename of saved universe dataset.
    """
    population_dict_json = {}
    for species in population_dict:
        population_dict_json[species] = {}
        population_dict_json[species]['statistics'] = population_dict[species]['statistics']
        population_dict_json[species]['organisms'] = [
            organism.to_dict()
            for organism in population_dict[species]['organisms']
        ]
    universe_dict = {
        'population': population_dict_json,
        'world': world.to_dict()
    }

    with open(fn, 'w') as f:
        json.dump(universe_dict, f, indent=2)

    log_dict = {
        'species': {
            species: population_dict[species]['statistics'] 
            for species in population_dict
        },
        'world': {
            'time': world.current_time
        }
    }
    with open(Path(fn).parent / f'log_{Path(fn).name}', 'w') as f:
        json.dump(log_dict, f, indent=2)
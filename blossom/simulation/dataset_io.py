"""
Load information from a certain dataset, e.g. to resume a simulation, and
write world and organism data back to file.
"""

import copy
import json
import pickle
from pathlib import Path
import numpy as np

from .world import World
from .organism import Organism


def load_universe(fn, seed=None):
    """
    Load dataset file from JSON.

    Parameters
    ----------
    fn : str
        Input filename of saved universe dataset
    seed : int, Generator, optional
        Random seed for the simulation

    Returns
    -------
    population_dict : dict
        A dict of Organism objects reconstructed from the saved dataset
    world : World
        World object reconstructed from the saved dataset
    rng : Generator
        Numpy random number generator from last timestep
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

    seed_fn = Path(fn).with_suffix('.seed')
    if seed is None and seed_fn.is_file():
        with open(seed_fn, 'rb') as f:
            rng = pickle.load(f)
    else:
        rng = np.random.default_rng(seed)

    return population_dict, world, rng


def save_universe(universe):
    """
    Save population_dict and world to file in JSON format.

    Parameters
    ----------
    universe : Universe
        Universe containing organism
    """
    padded_time = str(universe.current_time).zfill(universe.pad_zeros)
    data_fn = (
        universe.run_dir / f'data/{universe.run_dir.name}.{padded_time}.json'
    )
    log_fn = (
        universe.run_dir / f'logs/{universe.run_dir.name}.{padded_time}.log'
    )

    population_dict_json = {}
    for species in universe.population_dict:
        population_dict_json[species] = {}
        population_dict_json[species]['statistics'] = universe.population_dict[species]['statistics']
        population_dict_json[species]['organisms'] = [
            organism.to_dict()
            for organism in universe.population_dict[species]['organisms']
        ]
    universe_dict = {
        'population': population_dict_json,
        'world': universe.world.to_dict()
    }
    with open(data_fn, 'w') as f:
        json.dump(universe_dict, f, indent=2, cls=NPEncoder)

    log_dict = {
        'species': {
            species: universe.population_dict[species]['statistics'] 
            for species in universe.population_dict
        },
        'world': {
            'timestep': universe.world.current_time,
            'elapsed_time': universe.elapsed_time
        }
    }
    with open(log_fn, 'w') as f:
        json.dump(log_dict, f, indent=2)

    # Save seed information for last completed timestep
    last_padded_time = str(universe.current_time-1).zfill(universe.pad_zeros)
    last_seed_fn = (
        universe.run_dir / f'data/{universe.run_dir.name}.{last_padded_time}.seed'
    )
    last_seed_fn.unlink(missing_ok=True)
    seed_fn = (
        universe.run_dir / f'data/{universe.run_dir.name}.{padded_time}.seed'
    )
    with open(seed_fn, 'wb') as f:
        pickle.dump(universe.rng, f)


class NPEncoder(json.JSONEncoder):
    """
    Class to help serialize numpy types to json.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.floating):
            if np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super().default(obj)
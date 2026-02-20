"""
Load information from a certain dataset, e.g. to resume a simulation, and
write world and organism data back to file.
"""

import copy
import json
import pickle
import time
from pathlib import Path
from typing import Any
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
    seed : int, Generator
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
        seed = universe_dict['info']['initial_seed']
        with open(seed_fn, 'rb') as f:
            rng = pickle.load(f)
    else:
        if seed is None:
            seed = np.random.default_rng().integers(2**32)
        rng = np.random.default_rng(seed)
    config_params = {
        'initial_seed': seed,
        'rng': rng
    }

    return population_dict, world, config_params


def save_universe(
    universe,
    save_data: bool = True,
    save_log: bool = True,
    save_seed: bool = True,
    compact_json: bool = False
) -> dict[str, int | float]:
    """Save universe state to disk.

    Args:
        universe: Universe instance to serialize.
        save_data: Whether to write the timestep data snapshot (`.json`).
        save_log: Whether to write the timestep log snapshot (`.log`).
        save_seed: Whether to write the RNG seed snapshot (`.seed`).
        compact_json: Whether to write compact JSON without indentation.

    Returns:
        Dictionary of I/O statistics for this write call.
    """
    save_start = time.perf_counter()
    data_size = 0
    log_size = 0
    seed_size = 0
    files_written = 0

    if not (save_data or save_log or save_seed):
        return {
            'data_bytes': 0,
            'log_bytes': 0,
            'seed_bytes': 0,
            'total_bytes': 0,
            'files_written': 0,
            'write_time_s': 0.0
        }

    padded_time = str(universe.current_time).zfill(universe.pad_zeros)
    data_fn = (
        universe.run_data_dir / f'{universe.project_dir.name}.{padded_time}.json'
    )
    log_fn = (
        universe.run_logs_dir / f'{universe.project_dir.name}.{padded_time}.log'
    )
    dump_kwargs: dict[str, Any] = {'cls': NPEncoder}
    if compact_json:
        dump_kwargs['separators'] = (',', ':')
    else:
        dump_kwargs['indent'] = 2

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
        'world': universe.world.to_dict(),
        'info': {
            'initial_seed': universe.initial_seed
        }
    }
    if save_data:
        with open(data_fn, 'w') as f:
            json.dump(universe_dict, f, **dump_kwargs)
        data_size = data_fn.stat().st_size
        files_written += 1

    write_elapsed_prelog = time.perf_counter() - save_start
    if save_seed:
        # Preserve legacy behavior by keeping only the latest seed file.
        last_padded_time = str(universe.current_time-1).zfill(universe.pad_zeros)
        last_seed_fn = (
            universe.run_data_dir / f'{universe.project_dir.name}.{last_padded_time}.seed'
        )
        last_seed_fn.unlink(missing_ok=True)
        seed_fn = (
            universe.run_data_dir / f'{universe.project_dir.name}.{padded_time}.seed'
        )
        with open(seed_fn, 'wb') as f:
            pickle.dump(universe.rng, f)
        seed_size = seed_fn.stat().st_size
        files_written += 1

    if save_log:
        log_dict = {
            'species': {
                species: universe.population_dict[species]['statistics']
                for species in universe.population_dict
            },
            'world': {
                'timestep': universe.world.current_time,
                'elapsed_time': universe.elapsed_time
            },
            'performance': {
                'step_compute_time': getattr(universe, 'last_step_compute_time', 0.0),
                'step_write_time': write_elapsed_prelog,
                'running_compute_time': getattr(universe, 'total_compute_time', 0.0),
                'running_write_time': (
                    getattr(universe, 'total_write_time', 0.0) + write_elapsed_prelog
                ),
                'running_output_bytes': (
                    getattr(universe, 'total_output_bytes', 0) + data_size + seed_size
                ),
                'running_output_files': (
                    getattr(universe, 'total_output_files', 0) + files_written + 1
                ),
                'step_count': getattr(universe, 'step_count', 0),
                'saved': {
                    'data': save_data,
                    'seed': save_seed,
                    'log': save_log
                }
            },
            'info': {
                'initial_seed': universe.initial_seed,
                'size': data_size
            }
        }
        with open(log_fn, 'w') as f:
            json.dump(log_dict, f, **dump_kwargs)
        log_size = log_fn.stat().st_size
        files_written += 1

    write_elapsed = time.perf_counter() - save_start

    return {
        'data_bytes': data_size,
        'log_bytes': log_size,
        'seed_bytes': seed_size,
        'total_bytes': data_size + log_size + seed_size,
        'files_written': files_written,
        'write_time_s': write_elapsed
    }


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

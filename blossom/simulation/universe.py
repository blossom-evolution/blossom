import click 
import os
import yaml
from pathlib import Path
import datetime
from typing import Any

import time
import numpy as np

from . import parse_intent
from . import utils
from . import dataset_io as dio
from . import parameter_io as pio
from . import population_funcs as pf
from . import invariants


class Universe(object):
    """
    Create the universe of the simulation.
    """

    def __init__(self,
                 dataset_fn: str | Path | None = None,
                 config_fn: str | Path | None = None,
                 world_param_fn: str | Path | None = None,
                 species_param_fns: list[str] | str | Path | None = None,
                 world_param_dict: dict[str, Any] = {},
                 species_param_dicts: list[dict[str, Any]] = [{}],
                 custom_module_fns: list[str] | None = None,
                 current_time: int = 0,
                 end_time: int = 1000,
                 project_dir: str | Path = 'datasets/',
                 pad_zeros: int = 4,
                 seed=None,
                 **kwargs: Any) -> None:
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
        project_dir : str
            Overarching directory path for configuration and run files
        pad_zeros : int
            Number of zeroes to pad in dataset filenames
        seed : int, Generator, optional
            Random seed for the simulation
        """
        # Set random seeds for the entire simulation
        self.initial_seed = seed
        if seed is None:
            self.initial_seed = np.random.default_rng().integers(2**32)
        self.rng = np.random.default_rng(self.initial_seed)

        self.start_timestamp = time.time()
        self.last_timestamp = self.start_timestamp
        self.elapsed_time = 0
        self.last_step_compute_time = 0.0
        self.last_step_write_time = 0.0
        self.step_count = 0
        self.total_compute_time = 0.0
        self.total_write_time = 0.0
        self.total_data_bytes = 0
        self.total_log_bytes = 0
        self.total_seed_bytes = 0
        self.total_output_bytes = 0
        self.total_output_files = 0

        input_count = 0
        self.dataset_fn = dataset_fn
        if self.dataset_fn is not None:
            self.dataset_fn = Path(self.dataset_fn).resolve()
            input_count += 1

        self.config_fn = config_fn
        if self.config_fn is not None:
            self.config_fn = Path(self.config_fn).resolve()
            input_count += 1

        self.world_param_fn = world_param_fn
        self.species_param_fns = species_param_fns
        if self.world_param_fn is not None and self.species_param_fns is not None:
            self.world_param_fn = Path(self.world_param_fn).resolve()
            self.species_param_fns = Path(self.species_param_fns).resolve()
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


        self.current_time = current_time
        self.end_time = end_time
        self.pad_zeros = pad_zeros
        self.snapshot_interval = self._validate_interval(
            name='snapshot_interval',
            value=kwargs.get('snapshot_interval', 1),
            allow_none=False
        )
        self.log_interval = self._validate_interval(
            name='log_interval',
            value=kwargs.get('log_interval', 1),
            allow_none=False
        )
        self.retain_last_checkpoints = self._validate_interval(
            name='retain_last_checkpoints',
            value=kwargs.get('retain_last_checkpoints'),
            allow_none=True
        )
        self.compact_json_output = bool(kwargs.get('compact_json_output', False))
        self.validate_invariants = bool(kwargs.get('validate_invariants', False))

        self.initialize(seed=seed, project_dir=project_dir)
        self.organisms = pf.get_organism_list(self.population_dict)
        self.organisms_by_location = pf.hash_by_location(self.organisms)
        self.species_names = sorted(list(self.population_dict.keys()))
        self.intent_list = []
        self._step_last_organisms = None
        self._legacy_behavior_state_ready = False
        self._behavior_context_shared = None

        if self.validate_invariants:
            invariants.assert_step_invariants(self)

        self.organism_limit = kwargs.get('organism_limit')

    def _validate_interval(self, name: str, value: Any, allow_none: bool) -> int | None:
        """Validate interval-style configuration fields.

        Args:
            name: Name of the interval field.
            value: User-supplied value to validate.
            allow_none: Whether ``None`` is allowed.

        Returns:
            The validated integer value or ``None``.

        Raises:
            ValueError: If the value is not valid.
        """
        if value is None and allow_none:
            return None
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f'`{name}` must be a positive integer')
        return value

    def _should_write_snapshot(self) -> bool:
        """Return whether the current timestep should write a snapshot."""
        return self.current_time % self.snapshot_interval == 0

    def _should_write_log(self) -> bool:
        """Return whether the current timestep should write a log entry."""
        return self.current_time % self.log_interval == 0

    def _prune_checkpoints(self) -> None:
        """Prune old checkpoint data files based on retention policy."""
        if self.retain_last_checkpoints is None:
            return
        snapshot_fns = sorted(self.run_data_dir.glob('*.json'))
        if len(snapshot_fns) <= self.retain_last_checkpoints:
            return

        for old_fn in snapshot_fns[:-self.retain_last_checkpoints]:
            old_fn.unlink(missing_ok=True)
            old_fn.with_suffix('.seed').unlink(missing_ok=True)

    def _update_output_stats(self, io_stats: dict[str, int | float] | None) -> None:
        """
        Track cumulative output sizes and file counts for benchmarks.
        """
        if io_stats is None:
            return

        self.total_data_bytes += io_stats.get('data_bytes', 0)
        self.total_log_bytes += io_stats.get('log_bytes', 0)
        self.total_seed_bytes += io_stats.get('seed_bytes', 0)
        self.total_output_bytes += io_stats.get('total_bytes', 0)
        self.total_output_files += io_stats.get('files_written', 0)

    def _ensure_legacy_behavior_state(self) -> None:
        """
        Materialize aged per-step state for legacy callbacks on demand.

        Legacy callbacks receive the full ``universe`` object and may access
        ``universe.organisms``, ``universe.population_dict``, or
        ``universe.organisms_by_location``. Historically those were computed
        from an aged clone snapshot before intent generation. To preserve that
        behavior without paying the cost on every step, we build this snapshot
        only when a legacy callback is actually invoked.
        """
        if self._legacy_behavior_state_ready:
            return
        if self._step_last_organisms is None:
            return

        self.organisms = [organism.clone_self()._update_age()
                          for organism in self._step_last_organisms
                          if organism.alive]
        self.population_dict = pf.get_population_dict(self.organisms,
                                                      self.species_names)
        self.organisms_by_location = pf.hash_by_location(self.organisms)
        self._legacy_behavior_state_ready = True

    def _get_behavior_context_shared(self) -> dict[str, Any]:
        """
        Return per-step shared indexes used by intent-style callbacks.

        This cache avoids rebuilding ``organism_id -> organism`` and query
        indexes for every custom callback invocation in the same timestep.
        """
        if self._behavior_context_shared is not None:
            return self._behavior_context_shared

        step_source = self._step_last_organisms
        if step_source is None:
            step_source = self.organisms
            age_offset = 0
        else:
            age_offset = 1

        source_by_id: dict[str, Any] = {}
        ids_by_location: dict[tuple[int, ...], list[str]] = {}
        ids_by_species: dict[str, list[str]] = {}

        for organism in step_source:
            if age_offset == 1 and not organism.alive:
                continue
            organism_id = organism.organism_id
            source_by_id[organism_id] = organism

            location = tuple(organism.location)
            ids_by_location.setdefault(location, []).append(organism_id)
            ids_by_species.setdefault(organism.species_name, []).append(organism_id)

        self._behavior_context_shared = {
            "age_offset": age_offset,
            "source_by_id": source_by_id,
            "ids_by_location": ids_by_location,
            "ids_by_species": ids_by_species,
        }
        return self._behavior_context_shared

    def initialize(self, seed=None, project_dir=None) -> None:
        """
        Initialize world and organisms in the universe, from either saved
        datasets or from parameter files (and subsequently writing the
        initial time step to file).
        """
        if self.dataset_fn is not None:
            # Set up entire universe based on saved dataset
            self.population_dict, self.world, config_params = dio.load_universe(self.dataset_fn, 
                                                                                seed=seed)
            self.rng = config_params['rng']
            self.initial_seed = config_params['initial_seed']

            self.project_dir = self.dataset_fn.parents[2]
            self.run_data_dir = self.dataset_fn.parents[0]
            self.run_logs_dir = self.project_dir / 'logs' / self.run_data_dir.name
            self.run_logs_dir.mkdir(parents=True, exist_ok=True)
        else:
            if self.config_fn is not None:
                self.population_dict, self.world, config_params = pio.load_from_config(self.config_fn,
                                                                                       seed=seed)
                self.rng = config_params['rng']
                self.initial_seed = config_params['initial_seed']
                self.current_time = self.world.current_time
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
        
            # Save / directory structure
            self.project_dir = Path(project_dir).resolve()
            datestring = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            self.run_data_dir = self.project_dir / 'data' / f'{datestring}-s{self.initial_seed}'
            self.run_data_dir.mkdir(parents=True, exist_ok=True)
            self.run_logs_dir = self.project_dir / 'logs' / f'{datestring}-s{self.initial_seed}'
            self.run_logs_dir.mkdir(parents=True, exist_ok=True)
            io_stats = dio.save_universe(
                self,
                save_data=True,
                save_log=True,
                save_seed=True,
                compact_json=self.compact_json_output
            )
            self._update_output_stats(io_stats)
            self._prune_checkpoints()

    def step(self) -> None:
        """
        Steps through one time step, iterating over all organisms and
        computing new organism states. Saves all organisms and the world
        to file at the end of each step.
        """
        # Increment time step
        self.current_time += 1
        step_start = time.perf_counter()

        # This is just updating the age, not evaluating whether an organism
        # is at death, since organism actions should be evaluated based on
        # the current state. Age needs to be updated so that every organism
        # in intent list has the correct age.
        last_organisms = self.organisms
        self._step_last_organisms = last_organisms
        self._legacy_behavior_state_ready = False
        self._behavior_context_shared = None

        # intent_list is a list of lists, one list per organism in the current
        # time step
        self.intent_list = []
        try:
            for organism in last_organisms:
                if organism.alive:
                    # Actor age updates still occur in organism.step. Other
                    # organisms are exposed through BehaviorContext with a
                    # lazy aged baseline for intent-style callbacks.
                    self.intent_list.append(organism.step(self))

            # Parse intent list and ensure it is valid
            self.organisms = parse_intent.parse(self.intent_list,
                                                last_organisms,
                                                seed=self.rng)
        finally:
            # Per-step context cache should never leak across timesteps.
            self._step_last_organisms = None
            self._legacy_behavior_state_ready = False
            self._behavior_context_shared = None

        self.population_dict = pf.get_population_dict(self.organisms,
                                                      self.species_names)
        self.organisms_by_location = pf.hash_by_location(self.organisms)

        # Potential changes to the world would go here
        self.world.step()

        if self.validate_invariants:
            invariants.assert_step_invariants(self)

        compute_elapsed = time.perf_counter() - step_start
        self.last_step_compute_time = compute_elapsed
        self.step_count += 1
        self.total_compute_time += compute_elapsed

        # Save universe state
        # Always write terminal state so runs have a complete final snapshot/log.
        is_terminal_step = (self.current_time == self.end_time)
        write_snapshot = self._should_write_snapshot() or is_terminal_step
        write_log = self._should_write_log() or is_terminal_step
        if write_snapshot or write_log:
            io_stats = dio.save_universe(
                self,
                save_data=write_snapshot,
                save_log=write_log,
                save_seed=write_snapshot,
                compact_json=self.compact_json_output
            )
            if write_snapshot:
                self._prune_checkpoints()
        else:
            io_stats = {
                'data_bytes': 0,
                'log_bytes': 0,
                'seed_bytes': 0,
                'total_bytes': 0,
                'files_written': 0,
                'write_time_s': 0.0
            }
        write_elapsed = io_stats.get('write_time_s', 0.0)
        total_elapsed = compute_elapsed + write_elapsed

        self.last_step_write_time = write_elapsed
        self.elapsed_time = total_elapsed
        self.total_write_time += write_elapsed
        self._update_output_stats(io_stats)

        now = time.time()
        self.last_timestamp = now

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
        if verbosity >= 5:
            if expanded:
                pstring += (
                    '    Step compute time: %.3f ms\n'
                    % (1000 * self.last_step_compute_time)
                    + '    Step write time: %.3f ms\n'
                    % (1000 * self.last_step_write_time)
                    + '    Total output written: %.2f MB (%d files)\n'
                    % (self.total_output_bytes / (1024 ** 2),
                       self.total_output_files)
                )
            else:
                pstring += (
                    ' [compute=%.3fms, write=%.3fms, output=%.2fMB]'
                    % (1000 * self.last_step_compute_time,
                       1000 * self.last_step_write_time,
                       self.total_output_bytes / (1024 ** 2))
                )

        return pstring

    def run(self, verbosity=1, expanded=True):
        print(self.current_info(verbosity=verbosity, expanded=expanded))
        while self.current_time < self.end_time:
            self.step()
            print(self.current_info(verbosity=verbosity, expanded=expanded))

            if self.organism_limit is not None and len(self.organisms) > self.organism_limit:
                print(f'Exceeded organism limit! ({len(self.organisms)} '
                      f'> {self.organism_limit})')
                break


@click.command(name='run')
@click.option('-t', '--timesteps', default=1000,
              help='Max timestep')
@click.option('-l', '--organism_limit', type=int,
              help='Max number of organisms')
@click.option('-r', '--restart', is_flag=True, default=False,
              help='Option to erase past data files before run')
@click.option('-v', '--verbosity', default=4,
              help='Level of progress detail to print')
@click.option('-s', '--seed', type=int,
              help='Random seed')
@click.option('--snapshot_interval', type=int,
              help='Save full data snapshots every N timesteps')
@click.option('--log_interval', type=int,
              help='Save log files every N timesteps')
@click.option('--retain_last_checkpoints', type=int,
              help='Keep only the most recent N data checkpoints')
@click.option('--compact_json_output', is_flag=True, default=False,
              help='Write compact JSON output (smaller, faster writes)')
@click.option('--validate-invariants', is_flag=True, default=False,
              help='Validate timestep invariants on every step')
def run_universe(
    timesteps: int = 1000,
    organism_limit: int | None = None,
    restart: bool = False,
    verbosity: int = 4,
    seed: int | None = None,
    snapshot_interval: int | None = None,
    log_interval: int | None = None,
    retain_last_checkpoints: int | None = None,
    compact_json_output: bool = False,
    validate_invariants: bool = False
) -> None:
    """Run a simulation from a project directory configuration file.

    Args:
        timesteps: Maximum timestep to simulate.
        organism_limit: Optional organism-count safety limit.
        restart: Reserved flag for legacy restart behavior.
        verbosity: Level of console output detail.
        seed: Optional random seed override.
        snapshot_interval: Optional snapshot cadence override.
        log_interval: Optional log cadence override.
        retain_last_checkpoints: Optional retained checkpoint count.
        compact_json_output: Whether to write compact JSON output.
        validate_invariants: Whether to validate invariants every step.
    """
    project_dir = Path('.').resolve()

    # logs_path = project_dir / 'logs'
    # data_path = project_dir / 'data'

    # if data_path.is_dir():
    #     data_fns = sorted(data_path.glob('*.json'))
    #     if len(data_fns) > 0 and not restart:
    #         universe = Universe(dataset_fn=data_fns[-1], 
    #                             project_dir=project_dir,
    #                             end_time=timesteps, 
    #                             seed=seed,
    #                             organism_limit=organism_limit)
    #         universe.run(verbosity=verbosity, expanded=False)
    #         return

    # if restart:
    #     if logs_path.is_dir():
    #         for fn in logs_path.iterdir():
    #             fn.unlink()
    #     if data_path.is_dir():
    #         for fn in data_path.iterdir():
    #             fn.unlink()

    # Run even if not restarting, such as first run
    # Use .yml 
    config_path = list(project_dir.glob('*.yml'))
    if len(config_path) == 1:
        config_path = config_path[0]
        with open(config_path, 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        timesteps = cfg.get('timesteps', timesteps)
        organism_limit = cfg.get('organism_limit', organism_limit)
        snapshot_interval = cfg.get('snapshot_interval', snapshot_interval)
        log_interval = cfg.get('log_interval', log_interval)
        retain_last_checkpoints = cfg.get(
            'retain_last_checkpoints',
            retain_last_checkpoints
        )
        compact_json_output = cfg.get('compact_json_output', compact_json_output)
        validate_invariants = cfg.get('validate_invariants', validate_invariants)

        universe = Universe(config_fn=config_path, 
                            project_dir=project_dir,
                            end_time=timesteps, 
                            seed=seed,
                            organism_limit=organism_limit,
                            snapshot_interval=snapshot_interval,
                            log_interval=log_interval,
                            retain_last_checkpoints=retain_last_checkpoints,
                            compact_json_output=compact_json_output,
                            validate_invariants=validate_invariants)
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

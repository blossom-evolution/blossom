#!/usr/bin/env python3
"""
Run canonical Blossom benchmark scenarios (A/B/C) and summarize results.
"""

import argparse
import json
import platform
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import blossom  # noqa: E402

from summarize_run import summarize_run  # noqa: E402


@dataclass(frozen=True)
class Scenario:
    name: str
    total_population: int
    world_size: int
    timesteps: int


@dataclass(frozen=True)
class OutputSettings:
    snapshot_interval: int = 1
    log_interval: int = 1
    retain_last_checkpoints: int | None = None
    compact_json_output: bool = False


SCENARIOS = {
    'A': Scenario(name='A', total_population=100, world_size=50, timesteps=500),
    'B': Scenario(name='B', total_population=2000, world_size=100, timesteps=250),
    'C': Scenario(name='C', total_population=10000, world_size=200, timesteps=60),
}


def infer_hardware() -> dict[str, Any]:
    os_name = f"{platform.system()} {platform.release()}"
    machine = platform.machine()
    cpu = platform.processor() or 'unknown'
    memory_bytes = None

    if platform.system() == 'Darwin':
        try:
            cpu = subprocess.check_output(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                text=True
            ).strip()
        except Exception:
            pass
        try:
            memory_bytes = int(subprocess.check_output(
                ['sysctl', '-n', 'hw.memsize'],
                text=True
            ).strip())
        except Exception:
            pass

    memory_gb = None
    if memory_bytes is not None:
        memory_gb = memory_bytes / (1024 ** 3)

    return {
        'os': os_name,
        'machine': machine,
        'cpu': cpu,
        'memory_gb': memory_gb
    }


def build_config(
    scenario: Scenario,
    seed: int,
    output_settings: OutputSettings
) -> dict[str, Any]:
    species_a = scenario.total_population // 2
    species_b = scenario.total_population - species_a
    config: dict[str, Any] = {
        'seed': seed,
        'species': [
            {
                'name': 'species1',
                'population': species_a,
                'max_age': 'inf',
                'action': 'move_only',
                'movement': 'simple_random',
                'linked_modules': []
            },
            {
                'name': 'species2',
                'population': species_b,
                'max_age': 'inf',
                'action': 'move_only',
                'movement': 'simple_random',
                'linked_modules': []
            }
        ],
        'world': {
            'size': [scenario.world_size],
            'water': {'peak': 'inf'},
            'food': {'peak': 'inf'},
            'obstacles': {'peak': 0}
        },
        'timesteps': scenario.timesteps,
        'snapshot_interval': output_settings.snapshot_interval,
        'log_interval': output_settings.log_interval,
        'compact_json_output': output_settings.compact_json_output
    }
    if output_settings.retain_last_checkpoints is not None:
        config['retain_last_checkpoints'] = output_settings.retain_last_checkpoints
    return config


def run_once(
    project_dir: Path,
    scenario: Scenario,
    seed: int,
    output_settings: OutputSettings
) -> dict[str, Any]:
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / 'config.yml'
    with open(config_path, 'w') as f:
        yaml.safe_dump(build_config(scenario, seed, output_settings), f, sort_keys=False)

    run_start = time.perf_counter()
    universe = blossom.Universe(
        config_fn=config_path,
        project_dir=project_dir,
        end_time=scenario.timesteps,
        seed=seed,
        snapshot_interval=output_settings.snapshot_interval,
        log_interval=output_settings.log_interval,
        retain_last_checkpoints=output_settings.retain_last_checkpoints,
        compact_json_output=output_settings.compact_json_output
    )
    while universe.current_time < universe.end_time:
        universe.step()
    wall_runtime_s = time.perf_counter() - run_start

    summary = summarize_run(project_dir=project_dir, run_name=universe.run_data_dir.name)
    summary['wall_runtime_s'] = wall_runtime_s
    summary['seed'] = seed
    return summary


def aggregate(
    scenario_name: str,
    scenario: Scenario,
    runs: list[dict[str, Any]],
    seeds: list[int],
    output_settings: OutputSettings
) -> dict[str, Any]:
    def m(key):
        return mean(run[key] for run in runs)

    def mn(key):
        return min(run[key] for run in runs)

    def mx(key):
        return max(run[key] for run in runs)

    return {
        'scenario': scenario_name,
        'population': scenario.total_population,
        'world_size': scenario.world_size,
        'timesteps': scenario.timesteps,
        'repeats': len(runs),
        'seeds': seeds,
        'total_runtime_s_mean': m('total_runtime_s'),
        'timesteps_per_sec_mean': m('timesteps_per_sec'),
        'timesteps_per_sec_min': mn('timesteps_per_sec'),
        'timesteps_per_sec_max': mx('timesteps_per_sec'),
        'mean_step_compute_ms_mean': m('mean_step_compute_ms'),
        'mean_step_write_ms_mean': m('mean_step_write_ms'),
        'data_written_mb_mean': m('data_written_mb'),
        'files_created_mean': m('files_created'),
        'peak_run_disk_mb_mean': m('peak_run_disk_mb'),
        'output_settings': {
            'snapshot_interval': output_settings.snapshot_interval,
            'log_interval': output_settings.log_interval,
            'retain_last_checkpoints': output_settings.retain_last_checkpoints,
            'compact_json_output': output_settings.compact_json_output
        }
    }


def output_profile_label(output_settings: dict[str, Any]) -> str:
    """Describe output settings for markdown output labels."""
    if (
        output_settings['snapshot_interval'] == 1
        and output_settings['log_interval'] == 1
        and output_settings['retain_last_checkpoints'] is None
        and not output_settings['compact_json_output']
    ):
        return 'canonical baseline'
    return 'output controls enabled'


def to_benchmarks_row(record: dict[str, Any], commit_short: str) -> str:
    notes = (
        f"pop={record['population']}, world={record['world_size']}, "
        f"t={record['timesteps']}, n={record['repeats']}, "
        f"seeds={record['seeds']}, "
        f"snapshot={record['output_settings']['snapshot_interval']}, "
        f"log={record['output_settings']['log_interval']}, "
        f"retain={record['output_settings']['retain_last_checkpoints']}, "
        f"compact={record['output_settings']['compact_json_output']}, "
        f"tps range={record['timesteps_per_sec_min']:.3f}-{record['timesteps_per_sec_max']:.3f}"
    )
    return (
        f"| 2026-02-20 | {commit_short} | {record['scenario']} | "
        f"{output_profile_label(record['output_settings'])} | "
        f"{record['total_runtime_s_mean']:.6f} | "
        f"{record['timesteps_per_sec_mean']:.6f} | "
        f"{record['mean_step_compute_ms_mean']:.6f} | "
        f"{record['mean_step_write_ms_mean']:.6f} | "
        f"{record['data_written_mb_mean']:.6f} | "
        f"{int(round(record['files_created_mean']))} | "
        f"{record['peak_run_disk_mb_mean']:.6f} | "
        f"{notes} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description='Run canonical Blossom baselines')
    parser.add_argument('--scenario', choices=['A', 'B', 'C', 'all'], default='all',
                        help='Scenario to run')
    parser.add_argument('--repeats', type=int, default=3,
                        help='Number of repeats per scenario')
    parser.add_argument('--output-root', default=None,
                        help='Root directory for benchmark projects')
    parser.add_argument('--keep-artifacts', action='store_true',
                        help='Keep generated run directories')
    parser.add_argument('--seed-base', type=int, default=100,
                        help='Base seed value; repeat seeds are base+1..base+N')
    parser.add_argument('--snapshot-interval', type=int, default=1,
                        help='Save snapshots every N timesteps')
    parser.add_argument('--log-interval', type=int, default=1,
                        help='Save logs every N timesteps')
    parser.add_argument('--retain-last-checkpoints', type=int, default=None,
                        help='Keep only the latest N checkpoints')
    parser.add_argument('--compact-json-output', action='store_true',
                        help='Write compact JSON snapshots/logs')
    args = parser.parse_args()

    if args.repeats < 1:
        raise ValueError('--repeats must be >= 1')
    if args.snapshot_interval < 1:
        raise ValueError('--snapshot-interval must be >= 1')
    if args.log_interval < 1:
        raise ValueError('--log-interval must be >= 1')
    if args.retain_last_checkpoints is not None and args.retain_last_checkpoints < 1:
        raise ValueError('--retain-last-checkpoints must be >= 1')

    if args.output_root is None:
        output_root = Path(tempfile.mkdtemp(prefix='blossom-canonical-baselines-'))
    else:
        output_root = Path(args.output_root).resolve()
        output_root.mkdir(parents=True, exist_ok=True)

    selected = ['A', 'B', 'C'] if args.scenario == 'all' else [args.scenario]
    seeds = [args.seed_base + i + 1 for i in range(args.repeats)]
    output_settings = OutputSettings(
        snapshot_interval=args.snapshot_interval,
        log_interval=args.log_interval,
        retain_last_checkpoints=args.retain_last_checkpoints,
        compact_json_output=args.compact_json_output
    )
    commit_short = subprocess.check_output(
        ['git', '-C', str(Path(__file__).resolve().parents[2]), 'rev-parse', '--short', 'HEAD'],
        text=True
    ).strip()

    print(f'Output root: {output_root}')
    print(f'Scenarios: {selected}')
    print(f'Seeds: {seeds}')
    print(f'Output settings: {output_settings}')
    print(f'Commit: {commit_short}')

    scenario_records = []
    all_runs = {}
    for scenario_name in selected:
        scenario = SCENARIOS[scenario_name]
        runs = []
        for i, seed in enumerate(seeds, start=1):
            repeat_dir = output_root / f'{scenario_name}' / f'repeat_{i}'
            print(f'Running scenario {scenario_name} repeat {i}/{len(seeds)} (seed={seed})')
            summary = run_once(repeat_dir, scenario, seed, output_settings)
            runs.append(summary)
            if not args.keep_artifacts:
                shutil.rmtree(repeat_dir)
        all_runs[scenario_name] = runs
        scenario_records.append(aggregate(scenario_name, scenario, runs, seeds, output_settings))

    payload = {
        'date': '2026-02-20',
        'commit': commit_short,
        'python': platform.python_version(),
        'hardware': infer_hardware(),
        'output_root': str(output_root),
        'keep_artifacts': args.keep_artifacts,
        'output_settings': {
            'snapshot_interval': output_settings.snapshot_interval,
            'log_interval': output_settings.log_interval,
            'retain_last_checkpoints': output_settings.retain_last_checkpoints,
            'compact_json_output': output_settings.compact_json_output
        },
        'records': scenario_records,
        'runs': all_runs
    }
    result_path = output_root / 'canonical_baseline_results.json'
    with open(result_path, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f'Wrote results: {result_path}')

    print('\nMarkdown rows:')
    print('| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |')
    print('|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|')
    for record in scenario_records:
        print(to_benchmarks_row(record, commit_short))

    if not args.keep_artifacts:
        print('\nArtifacts were cleaned after each repeat. Only result JSON is retained.')
    print(f'Result directory: {output_root}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Summarize Blossom run metrics from generated log/data files.
"""

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def select_run_dir(project_dir: Path, run_name: str | None = None) -> Path:
    """Select a run directory under a project log root.

    Args:
        project_dir: Blossom project directory containing `logs/`.
        run_name: Optional explicit run directory name.

    Returns:
        Path to the selected run directory.
    """
    logs_root = project_dir / 'logs'
    if not logs_root.is_dir():
        raise FileNotFoundError(f'No logs directory found: {logs_root}')

    if run_name is not None:
        run_dir = logs_root / run_name
        if not run_dir.is_dir():
            raise FileNotFoundError(f'Run not found: {run_dir}')
        return run_dir

    run_dirs = [path for path in logs_root.glob('*') if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f'No run directories found in: {logs_root}')
    return max(run_dirs, key=lambda path: path.stat().st_mtime)


def load_logs(run_log_dir: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    """Load all JSON log files for a run directory."""
    log_paths = sorted(run_log_dir.glob('*.log'))
    if not log_paths:
        raise FileNotFoundError(f'No .log files in: {run_log_dir}')
    logs = []
    for path in log_paths:
        with open(path, 'r') as f:
            logs.append(json.load(f))
    return log_paths, logs


def summarize_run(project_dir: str | Path, run_name: str | None = None) -> dict[str, Any]:
    """Summarize runtime and output metrics for a single run.

    Args:
        project_dir: Blossom project directory containing `data/` and `logs/`.
        run_name: Optional explicit run directory name.

    Returns:
        Dictionary of summary metrics used in benchmark tables.
    """
    project_dir = Path(project_dir).resolve()
    run_log_dir = select_run_dir(project_dir, run_name=run_name)
    run_name = run_log_dir.name
    run_data_dir = project_dir / 'data' / run_name

    log_paths, logs = load_logs(run_log_dir)
    data_paths = sorted(run_data_dir.glob('*.json')) if run_data_dir.is_dir() else []
    seed_paths = sorted(run_data_dir.glob('*.seed')) if run_data_dir.is_dir() else []

    last_log = logs[-1]
    last_perf = last_log.get('performance', {})
    simulated_steps = int(last_perf.get('step_count', 0))

    running_compute = float(last_perf.get('running_compute_time', 0.0))
    running_write = float(last_perf.get('running_write_time', 0.0))
    total_runtime_s = running_compute + running_write
    if total_runtime_s <= 0:
        total_runtime_s = sum(entry.get('world', {}).get('elapsed_time', 0.0)
                              for entry in logs)
    if simulated_steps <= 0:
        timesteps = [entry.get('world', {}).get('timestep', 0) for entry in logs]
        simulated_steps = max(timesteps) - min(timesteps)
    timesteps_per_sec = simulated_steps / total_runtime_s if total_runtime_s > 0 else 0.0

    step_compute_times = [
        entry.get('performance', {}).get('step_compute_time')
        for entry in logs
        if entry.get('performance', {}).get('step_compute_time') is not None
    ]
    step_write_times = [
        entry.get('performance', {}).get('step_write_time')
        for entry in logs
        if entry.get('performance', {}).get('step_write_time') is not None
    ]
    if simulated_steps > 0 and running_compute > 0:
        mean_step_compute_ms = 1000.0 * running_compute / simulated_steps
    else:
        mean_step_compute_ms = 1000.0 * mean(step_compute_times) if step_compute_times else None
    if simulated_steps > 0 and running_write >= 0:
        mean_step_write_ms = 1000.0 * running_write / simulated_steps
    else:
        mean_step_write_ms = 1000.0 * mean(step_write_times) if step_write_times else None

    data_written_bytes = sum(path.stat().st_size for path in data_paths)
    log_written_bytes = sum(path.stat().st_size for path in log_paths)
    seed_written_bytes = sum(path.stat().st_size for path in seed_paths)
    total_written_bytes = data_written_bytes + log_written_bytes + seed_written_bytes
    files_created = len(data_paths) + len(log_paths) + len(seed_paths)

    summary = {
        'project_dir': str(project_dir),
        'run_name': run_name,
        'simulated_steps': simulated_steps,
        'total_runtime_s': total_runtime_s,
        'timesteps_per_sec': timesteps_per_sec,
        'mean_step_compute_ms': mean_step_compute_ms,
        'mean_step_write_ms': mean_step_write_ms,
        'data_written_mb': data_written_bytes / (1024 ** 2),
        'log_written_mb': log_written_bytes / (1024 ** 2),
        'seed_written_mb': seed_written_bytes / (1024 ** 2),
        'peak_run_disk_mb': total_written_bytes / (1024 ** 2),
        'files_created': files_created
    }
    return summary


def print_markdown_row(summary: dict[str, Any]) -> None:
    """Print a single benchmark markdown table row."""
    print(
        '| - | - | - | - | '
        f"{summary['total_runtime_s']:.6f} | "
        f"{summary['timesteps_per_sec']:.6f} | "
        f"{summary['mean_step_compute_ms'] if summary['mean_step_compute_ms'] is not None else 'n/a'} | "
        f"{summary['mean_step_write_ms'] if summary['mean_step_write_ms'] is not None else 'n/a'} | "
        f"{summary['data_written_mb']:.6f} | "
        f"{summary['files_created']} | "
        f"{summary['peak_run_disk_mb']:.6f} | "
        f"run={summary['run_name']} |"
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Summarize Blossom run metrics')
    parser.add_argument('--project-dir', default='.',
                        help='Path to Blossom project directory')
    parser.add_argument('--run-name', default=None,
                        help='Specific run directory name under logs/')
    parser.add_argument('--format', choices=['json', 'md'], default='json',
                        help='Output format')
    args = parser.parse_args()

    summary = summarize_run(project_dir=args.project_dir, run_name=args.run_name)
    if args.format == 'json':
        print(json.dumps(summary, indent=2))
    else:
        print_markdown_row(summary)


if __name__ == '__main__':
    main()

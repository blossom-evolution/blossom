"""Integration tests for deterministic seeded equivalence in Blossom."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from blossom.simulation import Universe, state_hash

SMALL_POPULATION = 8
SMALL_TIMESTEPS = 6


def _write_small_config(config_path: Path, *, seed: int, timesteps: int) -> None:
    """Write a small deterministic benchmark-style config.

    Args:
        config_path: Destination config path.
        seed: Seed for simulation determinism.
        timesteps: Number of timesteps in run.
    """
    cfg = {
        "seed": seed,
        "timesteps": timesteps,
        "snapshot_interval": 1,
        "log_interval": 1,
        "compact_json_output": True,
        "species": [
            {
                "name": "species1",
                "population": SMALL_POPULATION,
                "max_age": "inf",
                "action": "move_only",
                "movement": "simple_random",
                "linked_modules": [],
            },
            {
                "name": "species2",
                "population": SMALL_POPULATION,
                "max_age": "inf",
                "action": "move_only",
                "movement": "simple_random",
                "linked_modules": [],
            },
        ],
        "world": {
            "size": [20],
            "water": {"peak": "inf"},
            "food": {"peak": "inf"},
            "obstacles": {"peak": 0},
        },
    }
    with open(config_path, "w") as handle:
        yaml.safe_dump(cfg, handle, sort_keys=False)


def _run_project(project_dir: Path, *, seed: int, timesteps: int) -> Path:
    """Run one deterministic project and return its data directory.

    Args:
        project_dir: Project directory containing config and outputs.
        seed: Seed for simulation.
        timesteps: Number of timesteps to run.

    Returns:
        Data directory for the run.
    """
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / "config.yml"
    _write_small_config(config_path=config_path, seed=seed, timesteps=timesteps)

    universe = Universe(
        config_fn=config_path,
        project_dir=project_dir,
        end_time=timesteps,
        seed=seed,
        snapshot_interval=1,
        log_interval=1,
        compact_json_output=True,
        validate_invariants=True,
    )
    while universe.current_time < universe.end_time:
        universe.step()
    return universe.run_data_dir


def _extract_step(snapshot_path: Path) -> int:
    """Extract timestep from a Blossom snapshot filename.

    Args:
        snapshot_path: Snapshot file path.

    Returns:
        Integer timestep.
    """
    return int(snapshot_path.stem.split(".")[-1])


def _load_hashes(run_data_dir: Path) -> dict[int, str]:
    """Load per-step state hashes for a run directory.

    Args:
        run_data_dir: Directory containing snapshot JSON files.

    Returns:
        Mapping from timestep to state hash.
    """
    hashes: dict[int, str] = {}
    for snapshot_path in sorted(run_data_dir.glob("*.json")):
        with open(snapshot_path, "r") as handle:
            snapshot = json.load(handle)
        hashes[_extract_step(snapshot_path)] = state_hash(snapshot)
    return hashes


def _load_final_outcomes(run_data_dir: Path) -> dict[str, dict[str, Any]]:
    """Load final organism outcomes from a run directory.

    Args:
        run_data_dir: Directory containing snapshot JSON files.

    Returns:
        Final outcomes indexed by organism ID.
    """
    snapshots = sorted(run_data_dir.glob("*.json"))
    final_path = snapshots[-1]
    with open(final_path, "r") as handle:
        final_snapshot = json.load(handle)

    outcomes: dict[str, dict[str, Any]] = {}
    for species, payload in final_snapshot["population"].items():
        for organism in payload["organisms"]:
            outcomes[str(organism["organism_id"])] = {
                "species_name": species,
                "alive": organism["alive"],
                "cause_of_death": organism["cause_of_death"],
                "age_at_death": organism["age_at_death"],
            }
    return outcomes


@pytest.mark.integration
def test_small_seeded_runs_have_identical_state_hashes(tmp_path: Path) -> None:
    """Two identical seeded runs should match for every timestep hash."""
    left_dir = _run_project(tmp_path / "left", seed=314, timesteps=SMALL_TIMESTEPS)
    right_dir = _run_project(tmp_path / "right", seed=314, timesteps=SMALL_TIMESTEPS)

    assert _load_hashes(left_dir) == _load_hashes(right_dir)


@pytest.mark.integration
def test_small_seeded_runs_have_identical_final_outcomes(tmp_path: Path) -> None:
    """Two identical seeded runs should end with identical outcomes."""
    left_dir = _run_project(tmp_path / "left", seed=2718, timesteps=SMALL_TIMESTEPS)
    right_dir = _run_project(tmp_path / "right", seed=2718, timesteps=SMALL_TIMESTEPS)

    assert _load_final_outcomes(left_dir) == _load_final_outcomes(right_dir)

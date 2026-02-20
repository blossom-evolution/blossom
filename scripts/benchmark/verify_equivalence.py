#!/usr/bin/env python3
"""Verify equivalence between two Blossom runs.

This script compares timestep snapshots using canonical state hashes and
reports any divergence in shared timesteps, final snapshots, and final species
statistics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from blossom.simulation.invariants import state_hash  # noqa: E402


def select_run_data_dir(project_dir: Path, run_name: str | None) -> Path:
    """Select a run data directory under ``project_dir/data``.

    Args:
        project_dir: Project root containing a ``data`` directory.
        run_name: Explicit run directory name. If omitted, latest run is used.

    Returns:
        Path to selected run data directory.

    Raises:
        FileNotFoundError: If data root or run directory does not exist.
    """
    data_root = project_dir / "data"
    if not data_root.is_dir():
        raise FileNotFoundError(f"No data directory found: {data_root}")

    if run_name is not None:
        run_dir = data_root / run_name
        if not run_dir.is_dir():
            raise FileNotFoundError(f"Run not found: {run_dir}")
        return run_dir

    run_dirs = [path for path in data_root.glob("*") if path.is_dir()]
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found in: {data_root}")
    return max(run_dirs, key=lambda path: path.stat().st_mtime)


def extract_timestep(path: Path) -> int:
    """Extract integer timestep from a Blossom data filename."""
    # Example: project_name.0030.json -> timestep 30
    return int(path.stem.split(".")[-1])


def load_snapshots(run_data_dir: Path) -> dict[int, dict[str, Any]]:
    """Load all timestep snapshots from a run data directory."""
    snapshots: dict[int, dict[str, Any]] = {}
    for path in sorted(run_data_dir.glob("*.json")):
        timestep = extract_timestep(path)
        with open(path, "r") as handle:
            snapshots[timestep] = json.load(handle)
    if not snapshots:
        raise FileNotFoundError(f"No JSON snapshots found in: {run_data_dir}")
    return snapshots


def final_species_stats(snapshot: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Extract final species statistics from a snapshot."""
    population = snapshot.get("population", {})
    return {
        species: payload.get("statistics", {})
        for species, payload in population.items()
    }


def final_outcomes(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index organism terminal outcomes by ID from a snapshot."""
    outcomes: dict[str, dict[str, Any]] = {}
    population = snapshot.get("population", {})
    for species, payload in population.items():
        for organism in payload.get("organisms", []):
            organism_id = organism.get("organism_id")
            outcomes[str(organism_id)] = {
                "species_name": species,
                "alive": organism.get("alive"),
                "cause_of_death": organism.get("cause_of_death"),
                "age_at_death": organism.get("age_at_death"),
            }
    return outcomes


def compare_runs(
    left_snapshots: dict[int, dict[str, Any]],
    right_snapshots: dict[int, dict[str, Any]],
    require_all_steps: bool,
) -> dict[str, Any]:
    """Compare two snapshot maps and return structured results."""
    left_steps = set(left_snapshots.keys())
    right_steps = set(right_snapshots.keys())
    shared_steps = sorted(left_steps & right_steps)
    left_only_steps = sorted(left_steps - right_steps)
    right_only_steps = sorted(right_steps - left_steps)

    mismatched_hashes: list[dict[str, Any]] = []
    for timestep in shared_steps:
        left_hash = state_hash(left_snapshots[timestep])
        right_hash = state_hash(right_snapshots[timestep])
        if left_hash != right_hash:
            mismatched_hashes.append(
                {
                    "timestep": timestep,
                    "left_hash": left_hash,
                    "right_hash": right_hash,
                }
            )

    left_final_step = max(left_steps)
    right_final_step = max(right_steps)
    left_final = left_snapshots[left_final_step]
    right_final = right_snapshots[right_final_step]

    left_final_hash = state_hash(left_final)
    right_final_hash = state_hash(right_final)

    left_stats = final_species_stats(left_final)
    right_stats = final_species_stats(right_final)
    left_outcomes = final_outcomes(left_final)
    right_outcomes = final_outcomes(right_final)

    per_step_equal = not mismatched_hashes
    if require_all_steps:
        per_step_equal = per_step_equal and not left_only_steps and not right_only_steps

    summary = {
        "shared_step_count": len(shared_steps),
        "left_step_count": len(left_steps),
        "right_step_count": len(right_steps),
        "left_only_steps": left_only_steps,
        "right_only_steps": right_only_steps,
        "mismatched_hashes": mismatched_hashes,
        "final_left_step": left_final_step,
        "final_right_step": right_final_step,
        "final_left_hash": left_final_hash,
        "final_right_hash": right_final_hash,
        "per_step_equal": per_step_equal,
        "final_state_equal": left_final_hash == right_final_hash,
        "final_species_stats_equal": left_stats == right_stats,
        "final_outcomes_equal": left_outcomes == right_outcomes,
    }
    return summary


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Verify equivalence between two Blossom runs")
    parser.add_argument("--left-project", required=True, help="Left project directory")
    parser.add_argument("--right-project", required=True, help="Right project directory")
    parser.add_argument("--left-run-name", default=None, help="Optional left run name under data/")
    parser.add_argument("--right-run-name", default=None, help="Optional right run name under data/")
    parser.add_argument(
        "--require-all-steps",
        action="store_true",
        help="Require identical timestep sets in both runs",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    args = parser.parse_args()

    left_project = Path(args.left_project).resolve()
    right_project = Path(args.right_project).resolve()
    left_run_dir = select_run_data_dir(left_project, args.left_run_name)
    right_run_dir = select_run_data_dir(right_project, args.right_run_name)

    left_snapshots = load_snapshots(left_run_dir)
    right_snapshots = load_snapshots(right_run_dir)
    result = compare_runs(
        left_snapshots=left_snapshots,
        right_snapshots=right_snapshots,
        require_all_steps=args.require_all_steps,
    )
    result.update(
        {
            "left_project": str(left_project),
            "right_project": str(right_project),
            "left_run_dir": str(left_run_dir),
            "right_run_dir": str(right_run_dir),
        }
    )

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"left_run={left_run_dir.name} right_run={right_run_dir.name}")
        print(f"shared_steps={result['shared_step_count']}")
        print(f"per_step_equal={result['per_step_equal']}")
        print(f"final_state_equal={result['final_state_equal']}")
        print(f"final_species_stats_equal={result['final_species_stats_equal']}")
        print(f"final_outcomes_equal={result['final_outcomes_equal']}")
        print(f"mismatched_hashes={len(result['mismatched_hashes'])}")
        if result["mismatched_hashes"]:
            first = result["mismatched_hashes"][0]
            print(f"first_mismatch_timestep={first['timestep']}")

    success = (
        result["per_step_equal"]
        and result["final_state_equal"]
        and result["final_species_stats_equal"]
        and result["final_outcomes_equal"]
    )
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

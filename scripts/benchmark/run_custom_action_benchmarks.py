#!/usr/bin/env python3
"""Run benchmark scenarios comparing built-in vs custom-action workloads."""

from __future__ import annotations

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
    """Benchmark scenario settings."""

    name: str
    total_population: int
    world_size: int
    timesteps: int


@dataclass(frozen=True)
class OutputSettings:
    """Output settings that impact runtime and disk usage."""

    snapshot_interval: int = 1
    log_interval: int = 1
    retain_last_checkpoints: int | None = None
    compact_json_output: bool = False
    validate_invariants: bool = False


@dataclass(frozen=True)
class Workload:
    """Behavior workload profile for benchmark runs."""

    name: str
    description: str
    module_source: str | None


SCENARIOS: dict[str, Scenario] = {
    "A": Scenario(name="A", total_population=100, world_size=50, timesteps=500),
    "B": Scenario(name="B", total_population=2000, world_size=100, timesteps=250),
    "C": Scenario(name="C", total_population=10000, world_size=200, timesteps=60),
}


CUSTOM_ACTION_MODULE = """\
from blossom.simulation import BehaviorContext, OrganismView


def custom_move_action(org: OrganismView, ctx: BehaviorContext) -> str:
    \"\"\"Custom callback equivalent to built-in move-only action.\"\"\"
    del org, ctx
    return "move"
"""


CUSTOM_INTERACTION_MODULE = """\
from blossom.simulation import (
    BehaviorContext,
    CompositeIntent,
    FieldChange,
    OrganismView,
    UpdateIntent,
)


def predator_action(org: OrganismView, ctx: BehaviorContext) -> str:
    \"\"\"Predator hunts when prey is colocated, otherwise moves.\"\"\"
    colocated_prey = [
        prey
        for prey in ctx.at_location(tuple(org.location))
        if prey.alive and prey.species_name == "prey"
    ]
    return "eat" if colocated_prey else "move"


def prey_action(org: OrganismView, ctx: BehaviorContext) -> str:
    \"\"\"Simple prey movement policy.\"\"\"
    del org, ctx
    return "move"


def custom_eat_prey(org: OrganismView, ctx: BehaviorContext) -> CompositeIntent:
    \"\"\"Intent-style eating callback that kills one colocated prey.\"\"\"
    prey_candidates = [
        prey
        for prey in ctx.at_location(tuple(org.location))
        if prey.alive and prey.species_name == "prey"
    ]
    if not prey_candidates:
        return CompositeIntent(
            actor_id=org.organism_id,
            updates=(UpdateIntent(organism_id=org.organism_id, changes=()),),
        )

    prey = prey_candidates[0]
    diff = max(float(org.food_capacity or 0) - float(org.food_current or 0), 0.0)
    intake = min(10.0, diff)

    return CompositeIntent(
        actor_id=org.organism_id,
        updates=(
            UpdateIntent(
                organism_id=org.organism_id,
                changes=(FieldChange(field="food_current", op="add", value=intake),),
            ),
            UpdateIntent(
                organism_id=prey.organism_id,
                changes=(
                    FieldChange(field="alive", op="set", value=False),
                    FieldChange(field="cause_of_death", op="set", value="hunted"),
                    FieldChange(field="age_at_death", op="set", value=prey.age),
                ),
            ),
        ),
    )
"""


WORKLOADS: dict[str, Workload] = {
    "builtin": Workload(
        name="builtin",
        description="Built-in move_only baseline (no custom modules).",
        module_source=None,
    ),
    "custom_action": Workload(
        name="custom_action",
        description="Custom action callback that returns built-in move action.",
        module_source=CUSTOM_ACTION_MODULE,
    ),
    "custom_interaction": Workload(
        name="custom_interaction",
        description="Intent-style predator/prey interaction custom callbacks.",
        module_source=CUSTOM_INTERACTION_MODULE,
    ),
}


def infer_hardware() -> dict[str, Any]:
    """Collect lightweight hardware metadata for benchmark records."""
    os_name = f"{platform.system()} {platform.release()}"
    machine = platform.machine()
    cpu = platform.processor() or "unknown"
    memory_bytes = None

    if platform.system() == "Darwin":
        try:
            cpu = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
            ).strip()
        except Exception:
            pass
        try:
            memory_bytes = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"],
                text=True,
            ).strip())
        except Exception:
            pass

    memory_gb = None
    if memory_bytes is not None:
        memory_gb = memory_bytes / (1024 ** 3)

    return {
        "os": os_name,
        "machine": machine,
        "cpu": cpu,
        "memory_gb": memory_gb,
    }


def build_species_config(scenario: Scenario, workload: Workload) -> list[dict[str, Any]]:
    """Build species section for a scenario/workload pair."""
    species_a = scenario.total_population // 2
    species_b = scenario.total_population - species_a

    if workload.name == "builtin":
        return [
            {
                "name": "species1",
                "population": species_a,
                "max_age": "inf",
                "action": "move_only",
                "movement": "simple_random",
                "linked_modules": [],
            },
            {
                "name": "species2",
                "population": species_b,
                "max_age": "inf",
                "action": "move_only",
                "movement": "simple_random",
                "linked_modules": [],
            },
        ]

    if workload.name == "custom_action":
        return [
            {
                "name": "species1",
                "population": species_a,
                "max_age": "inf",
                "action": "custom_move_action",
                "movement": "simple_random",
                "linked_modules": ["custom_behaviors.py"],
            },
            {
                "name": "species2",
                "population": species_b,
                "max_age": "inf",
                "action": "custom_move_action",
                "movement": "simple_random",
                "linked_modules": ["custom_behaviors.py"],
            },
        ]

    if workload.name == "custom_interaction":
        return [
            {
                "name": "predator",
                "population": species_a,
                "max_age": "inf",
                "action": "predator_action",
                "movement": "simple_random",
                "eating": {
                    "type": "custom_eat_prey",
                    "capacity": 200,
                    "initial": 80,
                    "metabolism": 4,
                    "intake": 0,
                    "days_without": 20,
                },
                "linked_modules": ["custom_behaviors.py"],
            },
            {
                "name": "prey",
                "population": species_b,
                "max_age": "inf",
                "action": "prey_action",
                "movement": "simple_random",
                "linked_modules": ["custom_behaviors.py"],
            },
        ]

    raise ValueError(f"Unsupported workload: {workload.name}")


def build_config(
    scenario: Scenario,
    workload: Workload,
    seed: int,
    output_settings: OutputSettings,
) -> dict[str, Any]:
    """Build a benchmark config for one scenario/workload."""
    return {
        "seed": seed,
        "species": build_species_config(scenario=scenario, workload=workload),
        "world": {
            "size": [scenario.world_size],
            "water": {"peak": "inf"},
            "food": {"peak": "inf"},
            "obstacles": {"peak": 0},
        },
        "timesteps": scenario.timesteps,
        "snapshot_interval": output_settings.snapshot_interval,
        "log_interval": output_settings.log_interval,
        "compact_json_output": output_settings.compact_json_output,
        "validate_invariants": output_settings.validate_invariants,
    } | (
        {"retain_last_checkpoints": output_settings.retain_last_checkpoints}
        if output_settings.retain_last_checkpoints is not None
        else {}
    )


def run_once(
    project_dir: Path,
    scenario: Scenario,
    workload: Workload,
    seed: int,
    output_settings: OutputSettings,
) -> dict[str, Any]:
    """Run one benchmark repeat and return summarized metrics."""
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / "config.yml"
    with open(config_path, "w") as handle:
        yaml.safe_dump(
            build_config(
                scenario=scenario,
                workload=workload,
                seed=seed,
                output_settings=output_settings,
            ),
            handle,
            sort_keys=False,
        )

    if workload.module_source is not None:
        module_path = project_dir / "custom_behaviors.py"
        module_path.write_text(workload.module_source, encoding="utf-8")

    run_start = time.perf_counter()
    universe = blossom.Universe(
        config_fn=config_path,
        project_dir=project_dir,
        end_time=scenario.timesteps,
        seed=seed,
        snapshot_interval=output_settings.snapshot_interval,
        log_interval=output_settings.log_interval,
        retain_last_checkpoints=output_settings.retain_last_checkpoints,
        compact_json_output=output_settings.compact_json_output,
        validate_invariants=output_settings.validate_invariants,
    )
    while universe.current_time < universe.end_time:
        universe.step()
    wall_runtime_s = time.perf_counter() - run_start

    summary = summarize_run(project_dir=project_dir, run_name=universe.run_data_dir.name)
    summary["wall_runtime_s"] = wall_runtime_s
    summary["seed"] = seed
    return summary


def aggregate(
    workload_name: str,
    scenario_name: str,
    scenario: Scenario,
    runs: list[dict[str, Any]],
    seeds: list[int],
    output_settings: OutputSettings,
) -> dict[str, Any]:
    """Aggregate multiple repeats into one scenario/workload record."""

    def m(key: str) -> float:
        return mean(run[key] for run in runs)

    def mn(key: str) -> float:
        return min(run[key] for run in runs)

    def mx(key: str) -> float:
        return max(run[key] for run in runs)

    return {
        "workload": workload_name,
        "scenario": scenario_name,
        "population": scenario.total_population,
        "world_size": scenario.world_size,
        "timesteps": scenario.timesteps,
        "repeats": len(runs),
        "seeds": seeds,
        "total_runtime_s_mean": m("total_runtime_s"),
        "timesteps_per_sec_mean": m("timesteps_per_sec"),
        "timesteps_per_sec_min": mn("timesteps_per_sec"),
        "timesteps_per_sec_max": mx("timesteps_per_sec"),
        "mean_step_compute_ms_mean": m("mean_step_compute_ms"),
        "mean_step_write_ms_mean": m("mean_step_write_ms"),
        "data_written_mb_mean": m("data_written_mb"),
        "files_created_mean": m("files_created"),
        "peak_run_disk_mb_mean": m("peak_run_disk_mb"),
        "output_settings": {
            "snapshot_interval": output_settings.snapshot_interval,
            "log_interval": output_settings.log_interval,
            "retain_last_checkpoints": output_settings.retain_last_checkpoints,
            "compact_json_output": output_settings.compact_json_output,
            "validate_invariants": output_settings.validate_invariants,
        },
    }


def to_markdown_row(record: dict[str, Any], commit_short: str) -> str:
    """Convert one aggregate record into a benchmarks markdown row."""
    notes = (
        f"pop={record['population']}, world={record['world_size']}, "
        f"t={record['timesteps']}, n={record['repeats']}, "
        f"seeds={record['seeds']}, "
        f"snapshot={record['output_settings']['snapshot_interval']}, "
        f"log={record['output_settings']['log_interval']}, "
        f"retain={record['output_settings']['retain_last_checkpoints']}, "
        f"compact={record['output_settings']['compact_json_output']}, "
        f"validate={record['output_settings'].get('validate_invariants', False)}, "
        f"tps range={record['timesteps_per_sec_min']:.3f}-{record['timesteps_per_sec_max']:.3f}"
    )
    return (
        f"| 2026-02-20 | {commit_short} | {record['workload']} | {record['scenario']} | "
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
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Blossom benchmarks for custom action workloads"
    )
    parser.add_argument(
        "--workload",
        choices=["builtin", "custom_action", "custom_interaction", "all"],
        default="all",
        help="Workload profile to run",
    )
    parser.add_argument(
        "--scenario",
        choices=["A", "B", "C", "all"],
        default="B",
        help="Scenario to run",
    )
    parser.add_argument("--repeats", type=int, default=3,
                        help="Number of repeats per workload/scenario")
    parser.add_argument("--output-root", default=None,
                        help="Root directory for benchmark projects")
    parser.add_argument("--keep-artifacts", action="store_true",
                        help="Keep generated run directories")
    parser.add_argument("--seed-base", type=int, default=1000,
                        help="Base seed value; repeat seeds are base+1..base+N")
    parser.add_argument("--snapshot-interval", type=int, default=1,
                        help="Save snapshots every N timesteps")
    parser.add_argument("--log-interval", type=int, default=1,
                        help="Save logs every N timesteps")
    parser.add_argument("--retain-last-checkpoints", type=int, default=None,
                        help="Keep only latest N checkpoints")
    parser.add_argument("--compact-json-output", action="store_true",
                        help="Write compact JSON snapshots/logs")
    parser.add_argument("--validate-invariants", action="store_true",
                        help="Validate invariants each timestep (debug mode)")
    args = parser.parse_args()

    if args.repeats < 1:
        raise ValueError("--repeats must be >= 1")
    if args.snapshot_interval < 1:
        raise ValueError("--snapshot-interval must be >= 1")
    if args.log_interval < 1:
        raise ValueError("--log-interval must be >= 1")
    if args.retain_last_checkpoints is not None and args.retain_last_checkpoints < 1:
        raise ValueError("--retain-last-checkpoints must be >= 1")

    selected_workloads = (
        ["builtin", "custom_action", "custom_interaction"]
        if args.workload == "all"
        else [args.workload]
    )
    selected_scenarios = ["A", "B", "C"] if args.scenario == "all" else [args.scenario]
    seeds = [args.seed_base + i + 1 for i in range(args.repeats)]
    output_settings = OutputSettings(
        snapshot_interval=args.snapshot_interval,
        log_interval=args.log_interval,
        retain_last_checkpoints=args.retain_last_checkpoints,
        compact_json_output=args.compact_json_output,
        validate_invariants=args.validate_invariants,
    )

    if args.output_root is None:
        output_root = Path(tempfile.mkdtemp(prefix="blossom-custom-action-benchmarks-"))
    else:
        output_root = Path(args.output_root).resolve()
        output_root.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[2]
    commit_short = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
        text=True,
    ).strip()

    print(f"Output root: {output_root}")
    print(f"Workloads: {selected_workloads}")
    print(f"Scenarios: {selected_scenarios}")
    print(f"Seeds: {seeds}")
    print(f"Output settings: {output_settings}")
    print(f"Commit: {commit_short}")

    all_runs: dict[str, dict[str, list[dict[str, Any]]]] = {}
    records: list[dict[str, Any]] = []

    for workload_name in selected_workloads:
        workload = WORKLOADS[workload_name]
        all_runs[workload_name] = {}
        print(f"\n=== Workload: {workload_name} ===")
        print(f"Description: {workload.description}")

        for scenario_name in selected_scenarios:
            scenario = SCENARIOS[scenario_name]
            runs: list[dict[str, Any]] = []
            for i, seed in enumerate(seeds, start=1):
                repeat_dir = output_root / workload_name / scenario_name / f"repeat_{i}"
                print(
                    f"Running workload={workload_name} scenario={scenario_name} "
                    f"repeat {i}/{len(seeds)} (seed={seed})"
                )
                summary = run_once(
                    project_dir=repeat_dir,
                    scenario=scenario,
                    workload=workload,
                    seed=seed,
                    output_settings=output_settings,
                )
                runs.append(summary)
                if not args.keep_artifacts:
                    shutil.rmtree(repeat_dir)
            all_runs[workload_name][scenario_name] = runs
            records.append(
                aggregate(
                    workload_name=workload_name,
                    scenario_name=scenario_name,
                    scenario=scenario,
                    runs=runs,
                    seeds=seeds,
                    output_settings=output_settings,
                )
            )

    payload = {
        "date": "2026-02-20",
        "commit": commit_short,
        "python": platform.python_version(),
        "hardware": infer_hardware(),
        "output_root": str(output_root),
        "keep_artifacts": args.keep_artifacts,
        "output_settings": {
            "snapshot_interval": output_settings.snapshot_interval,
            "log_interval": output_settings.log_interval,
            "retain_last_checkpoints": output_settings.retain_last_checkpoints,
            "compact_json_output": output_settings.compact_json_output,
            "validate_invariants": output_settings.validate_invariants,
        },
        "records": records,
        "runs": all_runs,
    }
    result_path = output_root / "custom_action_benchmark_results.json"
    with open(result_path, "w") as handle:
        json.dump(payload, handle, indent=2)
    print(f"\nWrote results: {result_path}")

    print("\nMarkdown rows:")
    print("| Date | Commit | Workload | Scenario | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |")
    print("|------|--------|----------|----------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|")
    for record in records:
        print(to_markdown_row(record, commit_short))

    if not args.keep_artifacts:
        print("\nArtifacts were cleaned after each repeat. Only result JSON is retained.")
    print(f"Result directory: {output_root}")


if __name__ == "__main__":
    main()

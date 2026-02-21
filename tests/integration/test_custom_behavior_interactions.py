"""Integration tests for custom behavior callbacks that inspect other organisms."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from blossom.simulation import Universe


def _write_project_files(
    project_dir: Path,
    *,
    module_source: str,
    config: dict[str, Any],
) -> Path:
    """Write a temporary custom-behavior project.

    Args:
        project_dir: Project root for config/module/output.
        module_source: Python source for ``custom_behaviors.py``.
        config: Simulation config data to serialize as YAML.

    Returns:
        Path to the written config file.
    """
    project_dir.mkdir(parents=True, exist_ok=True)
    module_path = project_dir / "custom_behaviors.py"
    module_path.write_text(module_source, encoding="utf-8")

    config_path = project_dir / "config.yml"
    with open(config_path, "w") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
    return config_path


def _run_config(config_path: Path, *, project_dir: Path, seed: int, timesteps: int = 1) -> Universe:
    """Run a small simulation from config and return the final universe.

    Args:
        config_path: Path to ``config.yml``.
        project_dir: Output project directory.
        seed: Deterministic random seed.
        timesteps: Number of timesteps to run.

    Returns:
        Final universe state after running.
    """
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
    return universe


def test_intent_style_custom_hunt_uses_other_organisms_and_resolves_conflicts(
    tmp_path: Path,
) -> None:
    """Intent callbacks can inspect neighbors and remain parse-intent safe.

    Two predators target one prey in the same location. Both callbacks inspect
    co-located organisms via ``ctx.at_location`` and propose conflicting prey
    updates. The prey also proposes its own next state, so ``parse_intent``
    must choose exactly one non-conflicting proposal for the prey ID.
    """
    module_source = """
from blossom.simulation import BehaviorContext, CompositeIntent, FieldChange, OrganismView, UpdateIntent


def hunt(org: OrganismView, ctx: BehaviorContext) -> CompositeIntent:
    prey_candidates = [
        organism
        for organism in ctx.at_location(tuple(org.location))
        if organism.alive and organism.species_name == "prey"
    ]
    if not prey_candidates:
        return CompositeIntent(
            actor_id=org.organism_id,
            updates=(UpdateIntent(organism_id=org.organism_id, changes=()),),
        )

    prey = prey_candidates[0]
    return CompositeIntent(
        actor_id=org.organism_id,
        updates=(
            UpdateIntent(
                organism_id=org.organism_id,
                changes=(FieldChange(field="food_current", op="add", value=5),),
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

    config = {
        "seed": 41,
        "timesteps": 1,
        "species": [
            {
                "name": "predator",
                "population": 2,
                "max_age": "inf",
                "action": "hunt",
                "movement": "stationary",
                "eating": {
                    "type": "constant_eat",
                    "capacity": 100,
                    "initial": 10,
                    "metabolism": 1,
                    "intake": 0,
                    "days_without": 999,
                },
                "linked_modules": ["custom_behaviors.py"],
            },
            {
                "name": "prey",
                "population": 1,
                "max_age": 0,
                "action": "move_only",
                "movement": "stationary",
                "linked_modules": [],
            },
        ],
        "world": {
            "size": [1],
            "water": {"peak": "inf"},
            "food": {"peak": "inf"},
            "obstacles": {"peak": 0},
        },
    }

    config_path = _write_project_files(
        tmp_path / "intent_hunt_project",
        module_source=module_source,
        config=config,
    )
    universe = _run_config(
        config_path=config_path,
        project_dir=tmp_path / "intent_hunt_outputs",
        seed=41,
        timesteps=1,
    )

    predators = [organism for organism in universe.organisms if organism.species_name == "predator"]
    prey = [organism for organism in universe.organisms if organism.species_name == "prey"][0]

    assert len(predators) == 2
    assert prey.alive is False

    # Shared-prey conflicts can resolve to either:
    # 1) one predator hunt intent wins -> prey is hunted, one predator fed
    # 2) prey self-intent wins -> prey dies of old age, predators fallback
    food_values = sorted(organism.food_current for organism in predators)
    hunt_actions = sum(organism.last_action == "hunt" for organism in predators)
    if prey.cause_of_death == "hunted":
        assert food_values == [9, 14]
        assert hunt_actions == 1
    else:
        assert prey.cause_of_death == "old_age"
        assert food_values == [9, 9]
        assert hunt_actions == 0


def test_legacy_custom_callback_can_query_other_organisms_from_universe(
    tmp_path: Path,
) -> None:
    """Legacy callbacks can still inspect other organisms via universe indexes."""
    module_source = """
from blossom.simulation import legacy_behavior


@legacy_behavior
def panic(organism, universe):
    colocated = universe.organisms_by_location.get(tuple(organism.location), [])
    predators = [
        other
        for other in colocated
        if other.alive and other.species_name == "predator"
    ]
    if predators:
        return [organism.die("predator_contact")]
    return [organism]
"""

    config = {
        "seed": 77,
        "timesteps": 1,
        "species": [
            {
                "name": "predator",
                "population": 1,
                "max_age": "inf",
                "action": "move_only",
                "movement": "stationary",
                "linked_modules": [],
            },
            {
                "name": "prey",
                "population": 1,
                "max_age": "inf",
                "action": "panic",
                "movement": "stationary",
                "linked_modules": ["custom_behaviors.py"],
            },
        ],
        "world": {
            "size": [1],
            "water": {"peak": "inf"},
            "food": {"peak": "inf"},
            "obstacles": {"peak": 0},
        },
    }

    config_path = _write_project_files(
        tmp_path / "legacy_panic_project",
        module_source=module_source,
        config=config,
    )
    universe = _run_config(
        config_path=config_path,
        project_dir=tmp_path / "legacy_panic_outputs",
        seed=77,
        timesteps=1,
    )

    prey = [organism for organism in universe.organisms if organism.species_name == "prey"][0]
    assert prey.alive is False
    assert prey.cause_of_death == "predator_contact"

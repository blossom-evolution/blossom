"""Unit tests for Blossom's intent API dispatch and materialization helpers."""

from __future__ import annotations

import itertools
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from blossom.simulation import (
    CompositeIntent,
    FieldChange,
    Organism,
    OrganismView,
    SpawnIntent,
    UpdateIntent,
    legacy_behavior,
)
from blossom.simulation.intent_api import (
    BehaviorContext,
    invoke_behavior_callback,
    intent_behavior,
    normalize_effect_output,
)
from blossom.simulation.population_funcs import get_population_dict, hash_by_location
from blossom.simulation.world import World

_ORGANISM_SEED_COUNTER = itertools.count(123)


def _make_universe(organisms: list[Organism], seed: int = 7) -> Any:
    """Create a light-weight universe namespace for intent API tests.

    Args:
        organisms: Organisms for the universe.
        seed: RNG seed.

    Returns:
        Universe-like object containing fields required by intent helpers.
    """
    species_names = sorted({organism.species_name for organism in organisms})
    return SimpleNamespace(
        rng=np.random.default_rng(seed),
        world=World({"world_size": [10], "current_time": 0}),
        current_time=0,
        organisms=organisms,
        organisms_by_location=hash_by_location(organisms),
        population_dict=get_population_dict(organisms, species_names),
    )


def _make_organism(
    *,
    species_name: str,
    location: list[int],
    food_capacity: int | None = None,
    food_initial: int | None = None,
    food_current: int | None = None,
) -> Organism:
    """Create a test organism with deterministic IDs and optional food fields.

    Args:
        species_name: Species name for the organism.
        location: Initial location.
        food_capacity: Optional food capacity.
        food_initial: Optional initial food.
        food_current: Optional current food.

    Returns:
        Created organism.
    """
    init_dict: dict[str, Any] = {
        "species_name": species_name,
        "location": location,
        "movement_type": "stationary",
        "action_type": "move_only",
        "custom_module_fns": None,
    }
    if food_capacity is not None:
        init_dict["eating_type"] = "constant_eat"
        init_dict["food_capacity"] = food_capacity
        init_dict["food_initial"] = food_initial if food_initial is not None else food_capacity
        init_dict["food_current"] = food_current if food_current is not None else init_dict["food_initial"]
        init_dict["food_metabolism"] = 1
        init_dict["food_intake"] = 1
        init_dict["max_time_without_food"] = 99
    return Organism(init_dict=init_dict, seed=next(_ORGANISM_SEED_COUNTER))


def test_unmarked_callback_uses_new_org_ctx_contract() -> None:
    """Unmarked callbacks should receive read-only view/context by default."""
    actor = _make_organism(species_name="predator", location=[0])
    universe = _make_universe([actor])
    seen: dict[str, Any] = {}

    def callback(org: OrganismView, ctx: BehaviorContext) -> str:
        seen["org_type"] = type(org)
        seen["ctx_type"] = type(ctx)
        return "ok-new"

    result = invoke_behavior_callback(callback=callback, actor=actor, universe=universe)

    assert result == "ok-new"
    assert seen["org_type"] is OrganismView
    assert seen["ctx_type"] is BehaviorContext


def test_legacy_callback_requires_explicit_marker() -> None:
    """Legacy callbacks should execute only when marked with @legacy_behavior."""
    actor = _make_organism(species_name="predator", location=[0])
    universe = _make_universe([actor])

    @legacy_behavior
    def callback(organism: Organism, local_universe: Any) -> str:
        assert organism is actor
        assert local_universe is universe
        return "ok-legacy"

    result = invoke_behavior_callback(callback=callback, actor=actor, universe=universe)
    assert result == "ok-legacy"


def test_intent_and_legacy_markers_are_mutually_exclusive() -> None:
    """Callbacks cannot be marked as both intent and legacy."""

    def callback(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        return "unused"

    intent_marked = intent_behavior(callback)
    with pytest.raises(ValueError):
        legacy_behavior(intent_marked)


def test_normalize_effect_output_materializes_composite_updates() -> None:
    """Composite intents should be materialized into cloned organism updates."""
    actor = _make_organism(
        species_name="predator",
        location=[0],
        food_capacity=100,
        food_initial=50,
        food_current=50,
    )
    prey = _make_organism(
        species_name="prey",
        location=[0],
        food_capacity=40,
        food_initial=40,
        food_current=40,
    )
    universe = _make_universe([actor, prey])

    output = CompositeIntent(
        actor_id=actor.organism_id,
        updates=(
            UpdateIntent(
                organism_id=actor.organism_id,
                changes=(FieldChange(field="food_current", op="add", value=10),),
            ),
            UpdateIntent(
                organism_id=prey.organism_id,
                changes=(FieldChange(field="alive", op="set", value=False),),
            ),
        ),
    )
    affected = normalize_effect_output(output=output, actor=actor, universe=universe)
    by_id = {organism.organism_id: organism for organism in affected}

    assert by_id[actor.organism_id].food_current == 60
    assert by_id[prey.organism_id].alive is False
    # Ensure baseline objects were not mutated.
    assert actor.food_current == 50
    assert prey.alive is True


def test_normalize_effect_output_materializes_spawn_intent() -> None:
    """Spawn intents should produce child organisms from parents."""
    actor = _make_organism(species_name="predator", location=[0])
    universe = _make_universe([actor])

    output = CompositeIntent(
        actor_id=actor.organism_id,
        updates=(),
        spawns=(
            SpawnIntent(
                parent_ids=(actor.organism_id,),
                init_fields={"location": (1,), "species_name": "predator"},
            ),
        ),
    )
    affected = normalize_effect_output(output=output, actor=actor, universe=universe)

    assert len(affected) == 2
    child = next(organism for organism in affected if organism.organism_id != actor.organism_id)
    assert child.species_name == "predator"
    assert child.location == [1]


def test_normalize_effect_output_rejects_invalid_legacy_payload() -> None:
    """Invalid legacy payloads should fail with a clear error."""
    actor = _make_organism(species_name="predator", location=[0])
    universe = _make_universe([actor])

    with pytest.raises(TypeError):
        normalize_effect_output(output=[123], actor=actor, universe=universe)


def test_behavior_context_uses_step_baseline_with_age_offset() -> None:
    """Step contexts should expose age-incremented peers by default."""
    actor_source = _make_organism(species_name="predator", location=[0])
    peer_source = _make_organism(species_name="prey", location=[1])
    actor_source.age = 4
    peer_source.age = 9
    actor = actor_source.clone_self()._update_age()

    universe = _make_universe([actor_source, peer_source])
    universe._step_last_organisms = [actor_source, peer_source]

    context = BehaviorContext(universe=universe, actor=actor)
    peer_view = context.get_organism(peer_source.organism_id)
    actor_view = context.get_organism(actor.organism_id)

    assert peer_view.age == peer_source.age + 1
    assert actor_view.age == actor.age


def test_legacy_dispatch_invokes_universe_legacy_state_hook() -> None:
    """Legacy callbacks should request universe legacy step materialization."""
    actor = _make_organism(species_name="predator", location=[0])
    universe = _make_universe([actor])
    universe.called = False

    def _hook() -> None:
        universe.called = True

    universe._ensure_legacy_behavior_state = _hook

    @legacy_behavior
    def callback(organism: Organism, local_universe: Any) -> str:
        assert organism is actor
        assert local_universe is universe
        return "ok"

    result = invoke_behavior_callback(callback=callback, actor=actor, universe=universe)

    assert result == "ok"
    assert universe.called is True

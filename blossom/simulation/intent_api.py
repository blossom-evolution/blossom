"""Intent-oriented callback API for Blossom custom behaviors.

This module provides a native, engine-level intent representation for custom
behavior callbacks. Unmarked callbacks use the new intent-style input contract
(`OrganismView`, `BehaviorContext`) by default. Legacy callbacks using
(`Organism`, `Universe`) are still supported when explicitly decorated with
``@legacy_behavior``.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Literal, TypeVar

import numpy as np


IntentOp = Literal["set", "add", "subtract", "append"]

_INTENT_CALLBACK_MARKER = "_blossom_intent_behavior"
_LEGACY_CALLBACK_MARKER = "_blossom_legacy_behavior"
_FREEZE_WORLD_CACHE_SIZE = 4


@dataclass(frozen=True)
class FieldChange:
    """Represents one field mutation within an organism update.

    Attributes:
        field: Target organism attribute name.
        op: Mutation operation (`set`, `add`, `subtract`, `append`).
        value: Value used by `op`.
    """

    field: str
    op: IntentOp
    value: Any


@dataclass(frozen=True)
class UpdateIntent:
    """Represents ordered updates for a single organism.

    Attributes:
        organism_id: Target organism ID.
        changes: Ordered field-level updates.
    """

    organism_id: str
    changes: tuple[FieldChange, ...]


@dataclass(frozen=True)
class SpawnIntent:
    """Represents a proposed child/new organism creation.

    Attributes:
        parent_ids: Parent organism IDs (0, 1, or 2 IDs supported directly).
        init_fields: Field overrides applied to the spawned organism.
    """

    parent_ids: tuple[str, ...]
    init_fields: dict[str, Any]


@dataclass(frozen=True)
class CompositeIntent:
    """Represents all effects proposed by one actor for one decision step.

    Attributes:
        actor_id: Acting organism ID.
        updates: Proposed updates to existing organisms.
        spawns: Proposed newly created organisms.
    """

    actor_id: str
    updates: tuple[UpdateIntent, ...] = ()
    spawns: tuple[SpawnIntent, ...] = ()


CallbackT = TypeVar("CallbackT", bound=Callable[..., Any])


def intent_behavior(callback: CallbackT) -> CallbackT:
    """Mark a callback as intent-style (`OrganismView`, `BehaviorContext`).

    Args:
        callback: User callback to mark.

    Returns:
        The same callback, marked for intent-style invocation.
    """
    if is_legacy_behavior(callback):
        raise ValueError(
            "Callback cannot be marked as both intent and legacy behavior."
        )
    setattr(callback, _INTENT_CALLBACK_MARKER, True)
    return callback


def is_intent_behavior(callback: Callable[..., Any]) -> bool:
    """Return whether a callback is marked as intent-style."""
    return bool(getattr(callback, _INTENT_CALLBACK_MARKER, False))


def legacy_behavior(callback: CallbackT) -> CallbackT:
    """Mark a callback as legacy-style (`Organism`, `Universe`).

    Args:
        callback: User callback to mark.

    Returns:
        The same callback, marked for legacy-style invocation.
    """
    if is_intent_behavior(callback):
        raise ValueError(
            "Callback cannot be marked as both intent and legacy behavior."
        )
    setattr(callback, _LEGACY_CALLBACK_MARKER, True)
    return callback


def is_legacy_behavior(callback: Callable[..., Any]) -> bool:
    """Return whether a callback is marked as legacy-style."""
    return bool(getattr(callback, _LEGACY_CALLBACK_MARKER, False))


class OrganismView:
    """Read-only organism view used by intent-style callbacks."""

    __slots__ = ("_organism",)

    def __init__(self, organism: Any) -> None:
        object.__setattr__(self, "_organism", organism)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_organism":
            object.__setattr__(self, name, value)
            return
        raise AttributeError("OrganismView is read-only.")

    def __getattr__(self, name: str) -> Any:
        value = getattr(self._organism, name)
        return _freeze_value(value)


class WorldView:
    """Read-only world view used by intent-style callbacks."""

    __slots__ = ("_world", "_cache")

    def __init__(self, world: Any) -> None:
        object.__setattr__(self, "_world", world)
        object.__setattr__(self, "_cache", {})

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_world", "_cache"}:
            object.__setattr__(self, name, value)
            return
        raise AttributeError("WorldView is read-only.")

    def __getattr__(self, name: str) -> Any:
        cache = self._cache
        if name in cache:
            return cache[name]

        value = getattr(self._world, name)
        frozen = _freeze_value(value)
        if len(cache) < _FREEZE_WORLD_CACHE_SIZE:
            cache[name] = frozen
        return frozen


class BehaviorContext:
    """Read-only timestep context for intent-style custom callbacks.

    Args:
        universe: Active universe instance.
        actor: Current acting organism object.
    """

    def __init__(self, universe: Any, actor: Any) -> None:
        self.rng = universe.rng
        self.world = WorldView(universe.world)
        self.time = universe.current_time

        self._organisms_by_id: dict[str, Any] = {
            organism.organism_id: organism
            for organism in universe.organisms
        }
        # Ensure the actor reference exactly matches the currently stepping
        # actor object.
        self._organisms_by_id[actor.organism_id] = actor

        self._organisms_by_location = universe.organisms_by_location
        self._population_dict = universe.population_dict

    def _baseline(self, organism_id: str) -> Any:
        """Return the underlying organism object for internal use."""
        return self._organisms_by_id[organism_id]

    def view_for_id(self, organism_id: str) -> OrganismView:
        """Return a read-only organism view by organism ID."""
        return OrganismView(self._baseline(organism_id))

    def get_organism(self, organism_id: str) -> OrganismView:
        """Return a read-only organism view by organism ID."""
        return self.view_for_id(organism_id)

    def at_location(self, location: tuple[int, ...]) -> tuple[OrganismView, ...]:
        """Return read-only views for organisms at a location."""
        organisms = self._organisms_by_location.get(tuple(location), [])
        return tuple(OrganismView(organism) for organism in organisms)

    def by_species(
        self,
        species_name: str,
        alive_only: bool = True,
    ) -> tuple[OrganismView, ...]:
        """Return read-only organism views for a species.

        Args:
            species_name: Species key in population dict.
            alive_only: Whether to include only alive organisms.
        """
        species = self._population_dict.get(species_name)
        if species is None:
            return ()
        organisms = species["organisms"]
        if alive_only:
            organisms = [organism for organism in organisms if organism.alive]
        return tuple(OrganismView(organism) for organism in organisms)

    def nearest(
        self,
        source_id: str,
        k: int,
        species: str | None = None,
        alive_only: bool = True,
    ) -> tuple[OrganismView, ...]:
        """Return k-nearest organisms to `source_id` by Manhattan distance.

        Args:
            source_id: Source organism ID.
            k: Number of neighbors to return.
            species: Optional species filter.
            alive_only: Whether to include only alive organisms.

        Returns:
            Ordered tuple of organism views from nearest to farthest.
        """
        if k < 1:
            return ()

        source = self._baseline(source_id)
        source_location = tuple(source.location)

        candidates: list[tuple[int, str, Any]] = []
        for organism_id, organism in self._organisms_by_id.items():
            if organism_id == source_id:
                continue
            if alive_only and not organism.alive:
                continue
            if species is not None and organism.species_name != species:
                continue
            distance = _manhattan(source_location, tuple(organism.location))
            candidates.append((distance, organism_id, organism))

        candidates.sort(key=lambda item: (item[0], item[1]))
        return tuple(OrganismView(organism) for _, _, organism in candidates[:k])


def invoke_behavior_callback(callback: Callable[..., Any], actor: Any, universe: Any) -> Any:
    """Invoke a custom behavior callback using current API dispatch policy.

    Args:
        callback: Function loaded from a custom module.
        actor: Acting organism object.
        universe: Universe object.

    Returns:
        Callback result.
    """
    if is_legacy_behavior(callback):
        return callback(actor, universe)

    context = BehaviorContext(universe=universe, actor=actor)
    return callback(OrganismView(actor), context)


def materialize_composite_intent(intent: CompositeIntent, context: BehaviorContext, actor: Any) -> list[Any]:
    """Convert a composite intent into concrete organism outputs.

    Args:
        intent: Composite intent payload.
        context: Behavior context from the current timestep.
        actor: Acting organism object for this intent.

    Returns:
        List of concrete organism objects suitable for legacy parse flow.

    Raises:
        KeyError: If an update/spawn references an unknown organism ID.
        TypeError: If a field change uses an unsupported operation.
    """
    updated: dict[str, Any] = {}
    spawned: list[Any] = []

    def get_target_clone(organism_id: str) -> Any:
        if organism_id in updated:
            return updated[organism_id]
        if organism_id == actor.organism_id:
            baseline = actor
        else:
            baseline = context._baseline(organism_id)
        cloned = baseline.clone_self()
        updated[organism_id] = cloned
        return cloned

    for update in intent.updates:
        target = get_target_clone(update.organism_id)
        for change in update.changes:
            target = _apply_field_change(target, change)
        updated[update.organism_id] = target

    # Ensure actor is represented to avoid accidental no-action fallback when
    # callback intends to keep the actor unchanged.
    if intent.actor_id not in updated:
        updated[intent.actor_id] = actor.clone_self()

    for spawn in intent.spawns:
        child = _spawn_child(spawn=spawn, updated=updated, context=context)
        spawned.append(child)

    return [*updated.values(), *spawned]


def normalize_effect_output(output: Any, actor: Any, universe: Any) -> list[Any]:
    """Normalize legacy/object/intent callback output into organism objects.

    Args:
        output: Callback return value.
        actor: Acting organism object.
        universe: Active universe.

    Returns:
        Concrete organism list.

    Raises:
        TypeError: If callback returns an unsupported type.
    """
    if isinstance(output, CompositeIntent):
        context = BehaviorContext(universe=universe, actor=actor)
        return materialize_composite_intent(intent=output, context=context, actor=actor)

    if isinstance(output, (list, tuple)):
        organisms = list(output)
    else:
        organisms = [output]

    _validate_organism_output(organisms)
    return organisms


def _spawn_child(spawn: SpawnIntent, updated: dict[str, Any], context: BehaviorContext) -> Any:
    """Spawn one child organism from a spawn intent."""
    if spawn.parent_ids:
        primary_parent = _resolve_parent(spawn.parent_ids[0], updated, context)
        secondary_parent = None
        if len(spawn.parent_ids) >= 2:
            secondary_parent = _resolve_parent(spawn.parent_ids[1], updated, context)
        child = primary_parent.get_child(other_parent=secondary_parent, seed=context.rng)
    else:
        from .organism import Organism

        child = Organism(init_dict={}, seed=context.rng)

    for key, value in spawn.init_fields.items():
        child = child.update_parameter(
            parameter=key,
            value=_thaw_value(key, value),
            method="set",
        )
    return child


def _resolve_parent(parent_id: str, updated: dict[str, Any], context: BehaviorContext) -> Any:
    """Resolve parent organism by ID from updated or baseline state."""
    if parent_id in updated:
        return updated[parent_id]
    return context._baseline(parent_id)


def _apply_field_change(organism: Any, change: FieldChange) -> Any:
    """Apply one field change to a cloned organism."""
    value = _thaw_value(change.field, change.value)
    return organism.update_parameter(
        parameter=change.field,
        value=value,
        method=change.op,
    )


def _validate_organism_output(organisms: list[Any]) -> None:
    """Validate that callback output contains only Organism objects."""
    from .organism import Organism

    for organism in organisms:
        if not isinstance(organism, Organism):
            raise TypeError(
                "Custom behavior output must contain Organism objects or "
                "return CompositeIntent."
            )


def _manhattan(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    """Compute Manhattan distance for two location tuples."""
    if len(a) != len(b):
        raise ValueError("Location dimensionality mismatch.")
    return sum(abs(x - y) for x, y in zip(a, b))


def _freeze_value(value: Any) -> Any:
    """Recursively freeze a value for read-only callback exposure."""
    if isinstance(value, np.ndarray):
        view = value.view()
        view.setflags(write=False)
        return view
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, dict):
        frozen = {key: _freeze_value(val) for key, val in value.items()}
        return MappingProxyType(frozen)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _thaw_value(field: str, value: Any) -> Any:
    """Normalize intent values before update application."""
    if field == "location" and isinstance(value, tuple):
        return list(value)
    return value

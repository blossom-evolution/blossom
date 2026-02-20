# Custom Intent API Proposal

Last updated: 2026-02-20

## 1) Why

Current custom behavior is expressive, but callbacks can accidentally mutate
shared global structures before conflict resolution. We want:

- `parse_intent` to remain the single consistency boundary.
- Custom behavior to keep rich organism interactions.
- A safer interface that separates reads from proposed writes.

## 2) Design Summary

Use a hybrid callback interface:

1. Read simulation state via a read-only query context.
2. Return explicit intent records (or legacy organism objects).
3. Normalize all outputs into a common intent structure.
4. Keep existing `parse_intent` conflict policy (ID overlap winner selection).

## 3) Proposed Callback Context (Read-Only)

```python
class BehaviorContext(Protocol):
    rng: np.random.Generator
    world: WorldView
    time: int

    def at_location(self, location: tuple[int, ...]) -> tuple["OrganismView", ...]: ...
    def by_species(self, species_name: str, alive_only: bool = True) -> tuple["OrganismView", ...]: ...
    def nearest(
        self,
        source_id: str,
        k: int,
        species: str | None = None,
        alive_only: bool = True
    ) -> tuple["OrganismView", ...]: ...
```

Notes:

- Views are immutable snapshots for the current timestep.
- Custom code can inspect any organism/world field.
- No direct mutation of global collections.

## 4) Proposed Intent Types

```python
from dataclasses import dataclass
from typing import Any, Literal

IntentOp = Literal["set", "add", "subtract", "append"]

@dataclass(frozen=True)
class FieldChange:
    field: str
    op: IntentOp
    value: Any

@dataclass(frozen=True)
class UpdateIntent:
    organism_id: str
    changes: tuple[FieldChange, ...]

@dataclass(frozen=True)
class SpawnIntent:
    parent_ids: tuple[str, ...]
    init_fields: dict[str, Any]

@dataclass(frozen=True)
class CompositeIntent:
    """All effects proposed by one actor for one action selection."""
    actor_id: str
    updates: tuple[UpdateIntent, ...] = ()
    spawns: tuple[SpawnIntent, ...] = ()
```

## 5) Callback Signatures

## New-style (preferred)

```python
def predator_action(org: OrganismView, ctx: BehaviorContext) -> CompositeIntent | str:
    ...
```

Rules:

- Returning `str` keeps existing action-selection ergonomics (`"move"`, `"eat"`, ...).
- Returning `CompositeIntent` allows direct advanced behavior.

## Legacy (still supported)

```python
@legacy_behavior
def eat_prey(org: Organism, universe: Universe) -> list[Organism]:
    ...
```

Legacy outputs remain supported and are normalized in engine runtime.

## 6) Runtime Strategy (Implemented in Core)

Normalization pipeline:

1. If callback is marked with `@legacy_behavior`, invoke with
   legacy `(Organism, Universe)`.
2. Otherwise invoke with new `(OrganismView, BehaviorContext)` inputs.
3. If callback returns `CompositeIntent`, materialize to concrete organism
   objects in core runtime.
4. If callback returns `list[Organism]`, keep legacy behavior.
5. Feed resolved organism sets to existing `parse_intent` conflict policy.

This keeps current scripts valid while enabling native intent callbacks with
no sample-side adapter.

## 7) Conflict Resolution Semantics

Unchanged core idea:

- Each actor proposes one candidate set of organism outcomes.
- `parse_intent` selects non-overlapping candidate sets by organism IDs.
- Non-selected alive organisms advance with no-action progression.

Implementation detail may shift from object lists to intent sets, but
resolution policy remains equivalent.

## 8) Predator-Prey Example (New-Style)

Current intent effect from `sample_scripts/predator_prey/predator_eating.py`:

- predator gains food
- chosen prey dies

Equivalent new-style output:

```python
CompositeIntent(
    actor_id=predator.organism_id,
    updates=(
        UpdateIntent(
            organism_id=predator.organism_id,
            changes=(FieldChange("food_current", "add", intake),)
        ),
        UpdateIntent(
            organism_id=prey.organism_id,
            changes=(
                FieldChange("alive", "set", False),
                FieldChange("cause_of_death", "set", "eaten"),
                FieldChange("age_at_death", "set", prey.age),
            ),
        ),
    ),
)
```

## 9) Safety Guarantees

- Query context is read-only for global state.
- Proposed writes are explicit and auditable.
- Commit phase is the only mutating phase for canonical state.
- Invariant checks run after commit (ID uniqueness, index consistency).

## 10) Migration Plan

1. Add intent data classes and normalization layer.
2. Keep legacy callback path available through `@legacy_behavior`.
3. Treat new-style `(org, ctx)` as default callback contract.
4. Move docs/examples to new-style once parity is proven.
5. Keep legacy support until deprecation decision is made.

## 11) Open Questions

- Should strict mode reject unknown fields, or allow dynamic attributes?
- Should legacy adapter run full object diffs or tracked field diffs only?
- Should conflict selection remain purely random shuffle, or support policy hooks?

## 12) Working Sample

An executable sample scaffold is available in:

- `sample_scripts/predator_prey_v2/`

It demonstrates:

- New-style intent callbacks using default `(org, ctx)` invocation.
- Direct `CompositeIntent` return values in custom behavior logic.
- A runnable config and simulation entrypoint for iterative development.

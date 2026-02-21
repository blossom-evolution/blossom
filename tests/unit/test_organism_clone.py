"""Unit tests for organism cloning semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from blossom.simulation import Organism


def _make_organism(extra_fields: dict[str, Any] | None = None) -> Organism:
    """Build a minimal organism for clone tests.

    Args:
        extra_fields: Optional field overrides and custom fields.

    Returns:
        Initialized organism.
    """
    init_dict: dict[str, Any] = {
        "species_name": "clone_test_species",
        "location": [0],
        "movement_type": "stationary",
        "action_type": "move_only",
        # Keep attribute present to avoid constructor edge cases.
        "custom_module_fns": None,
    }
    if extra_fields is not None:
        init_dict.update(extra_fields)
    return Organism(init_dict=init_dict, seed=17)


def test_clone_deep_copies_mutable_containers() -> None:
    """Clone should not share list/dict/set containers with the source."""
    organism = _make_organism(
        {
            "location": [3],
            "ancestry": ["p0"],
            "custom_list": [1, {"nested": [10, 20]}],
            "custom_dict": {"a": [1, 2], "b": {"inner": 7}},
            "custom_set": {("x", 1), ("y", 2)},
        }
    )
    clone = organism.clone_self()

    # Top-level container identity isolation.
    assert clone.location is not organism.location
    assert clone.ancestry is not organism.ancestry
    assert clone.custom_list is not organism.custom_list
    assert clone.custom_dict is not organism.custom_dict
    assert clone.custom_set is not organism.custom_set

    # Nested container identity isolation.
    assert clone.custom_list[1] is not organism.custom_list[1]
    assert clone.custom_list[1]["nested"] is not organism.custom_list[1]["nested"]
    assert clone.custom_dict["a"] is not organism.custom_dict["a"]
    assert clone.custom_dict["b"] is not organism.custom_dict["b"]

    # Mutating clone must not mutate source.
    clone.location[0] = 99
    clone.ancestry.append("p1")
    clone.custom_list[1]["nested"].append(30)
    clone.custom_dict["a"].append(3)
    clone.custom_dict["b"]["inner"] = -1
    clone.custom_set.add(("z", 3))

    assert organism.location == [3]
    assert organism.ancestry == ["p0"]
    assert organism.custom_list[1]["nested"] == [10, 20]
    assert organism.custom_dict["a"] == [1, 2]
    assert organism.custom_dict["b"]["inner"] == 7
    assert ("z", 3) not in organism.custom_set


def test_clone_keeps_module_references_but_not_module_list(tmp_path: Path) -> None:
    """Clone should isolate module list container while reusing module refs."""
    module_path = tmp_path / "custom_behavior.py"
    module_path.write_text(
        "def move_only(org, ctx):\n"
        "    return []\n",
        encoding="utf-8",
    )

    organism = _make_organism({"custom_module_fns": [str(module_path)]})
    clone = organism.clone_self()

    assert hasattr(organism, "_custom_modules")
    assert hasattr(clone, "_custom_modules")
    assert organism._custom_modules is not clone._custom_modules
    assert organism._custom_modules[0] is clone._custom_modules[0]


def test_clone_fails_fast_for_non_deepcopyable_attributes() -> None:
    """Clone should fail clearly when custom attributes cannot be deep-copied."""

    class NonCopyable:
        def __deepcopy__(self, memo: dict[int, object]) -> object:
            del memo
            raise TypeError("cannot deepcopy")

    organism = _make_organism({"custom_object": NonCopyable()})
    with pytest.raises(TypeError, match="deepcopy-compatible"):
        organism.clone_self()

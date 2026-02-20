"""Invariant and equivalence utilities for Blossom simulation correctness."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any


def check_step_invariants(universe: Any) -> list[str]:
    """Validate core universe invariants for the current timestep.

    Args:
        universe: Universe instance to validate.

    Returns:
        A list of human-readable invariant violations. An empty list means all
        checks passed.
    """
    issues: list[str] = []
    organisms = list(universe.organisms)

    issues.extend(_check_unique_ids(organisms))
    issues.extend(_check_locations_in_bounds(organisms, universe.world.world_size))
    issues.extend(_check_population_dict(organisms, universe.population_dict, universe.species_names))
    issues.extend(_check_location_index(organisms, universe.organisms_by_location))

    if universe.world.current_time != universe.current_time:
        issues.append(
            "World/universe timestep mismatch: "
            f"world.current_time={universe.world.current_time}, "
            f"universe.current_time={universe.current_time}"
        )
    return issues


def assert_step_invariants(universe: Any) -> None:
    """Raise on invariant violations for a universe timestep."""
    issues = check_step_invariants(universe)
    if issues:
        message = "Step invariants failed:\n- " + "\n- ".join(issues)
        raise AssertionError(message)


def canonicalize_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical snapshot structure for deterministic hashing.

    Args:
        snapshot: Parsed timestep JSON snapshot.

    Returns:
        Canonicalized snapshot dictionary with deterministic ordering for
        species keys and organism entries.
    """
    canonical: dict[str, Any] = {}

    population = snapshot.get("population", {})
    canonical_population: dict[str, Any] = {}
    for species_name in sorted(population.keys()):
        species_payload = population[species_name]
        organisms = list(species_payload.get("organisms", []))
        organisms.sort(key=lambda organism: str(organism.get("organism_id", "")))
        canonical_population[species_name] = {
            "statistics": _canonicalize_obj(species_payload.get("statistics", {})),
            "organisms": [_canonicalize_obj(organism) for organism in organisms],
        }
    canonical["population"] = canonical_population

    for key in sorted(snapshot.keys()):
        if key == "population":
            continue
        canonical[key] = _canonicalize_obj(snapshot[key])
    return canonical


def state_hash(snapshot: dict[str, Any]) -> str:
    """Compute a deterministic digest for a timestep snapshot.

    Args:
        snapshot: Parsed timestep JSON snapshot.

    Returns:
        Hex SHA-256 digest string.
    """
    canonical = canonicalize_snapshot(snapshot)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _check_unique_ids(organisms: list[Any]) -> list[str]:
    """Check organism ID uniqueness."""
    counts: dict[str, int] = defaultdict(int)
    for organism in organisms:
        counts[organism.organism_id] += 1
    duplicates = sorted([organism_id for organism_id, count in counts.items() if count > 1])
    if duplicates:
        return [f"Duplicate organism IDs present: {duplicates[:10]}"]
    return []


def _check_locations_in_bounds(organisms: list[Any], world_size: list[int]) -> list[str]:
    """Check each organism location is in world bounds."""
    issues: list[str] = []
    ndim = len(world_size)
    for organism in organisms:
        location = organism.location
        if len(location) != ndim:
            issues.append(
                f"Organism {organism.organism_id} has invalid dimensionality: "
                f"{location} (expected {ndim} dims)"
            )
            continue
        for axis, bound in enumerate(world_size):
            coord = location[axis]
            if coord < 0 or coord >= bound:
                issues.append(
                    f"Organism {organism.organism_id} out of bounds at axis {axis}: "
                    f"{coord} not in [0, {bound - 1}]"
                )
    return issues


def _check_population_dict(
    organisms: list[Any],
    population_dict: dict[str, dict[str, Any]],
    species_names: list[str],
) -> list[str]:
    """Validate population dict stats and organism lists."""
    issues: list[str] = []

    expected_by_species: dict[str, list[Any]] = {species: [] for species in species_names}
    for organism in organisms:
        expected_by_species.setdefault(organism.species_name, []).append(organism)

    expected_species = set(expected_by_species.keys())
    actual_species = set(population_dict.keys())
    if expected_species != actual_species:
        missing = sorted(expected_species - actual_species)
        extra = sorted(actual_species - expected_species)
        issues.append(
            "Population species mismatch: "
            f"missing={missing or []}, extra={extra or []}"
        )

    for species_name in sorted(expected_species | actual_species):
        expected_orgs = expected_by_species.get(species_name, [])
        payload = population_dict.get(species_name)
        if payload is None:
            continue

        listed_orgs = payload.get("organisms", [])
        listed_ids = sorted(organism.organism_id for organism in listed_orgs)
        expected_ids = sorted(organism.organism_id for organism in expected_orgs)
        if listed_ids != expected_ids:
            issues.append(f"Population list mismatch for species '{species_name}'.")

        alive = sum(1 for organism in expected_orgs if organism.alive)
        dead = len(expected_orgs) - alive
        stats = payload.get("statistics", {})
        if stats.get("total") != len(expected_orgs):
            issues.append(
                f"Population stats mismatch for '{species_name}': "
                f"total={stats.get('total')} expected={len(expected_orgs)}"
            )
        if stats.get("alive") != alive:
            issues.append(
                f"Population stats mismatch for '{species_name}': "
                f"alive={stats.get('alive')} expected={alive}"
            )
        if stats.get("dead") != dead:
            issues.append(
                f"Population stats mismatch for '{species_name}': "
                f"dead={stats.get('dead')} expected={dead}"
            )

    return issues


def _check_location_index(
    organisms: list[Any],
    organisms_by_location: dict[tuple[int, ...], list[Any]],
) -> list[str]:
    """Validate organisms_by_location index consistency."""
    issues: list[str] = []

    expected: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for organism in organisms:
        expected[tuple(organism.location)].append(organism.organism_id)
    actual: dict[tuple[int, ...], list[str]] = {
        location: [organism.organism_id for organism in items]
        for location, items in organisms_by_location.items()
    }

    if set(expected.keys()) != set(actual.keys()):
        missing = sorted(set(expected.keys()) - set(actual.keys()))
        extra = sorted(set(actual.keys()) - set(expected.keys()))
        issues.append(
            "Location index key mismatch: "
            f"missing={missing[:10]}, extra={extra[:10]}"
        )

    for location in set(expected.keys()) | set(actual.keys()):
        expected_ids = sorted(expected.get(location, []))
        actual_ids = sorted(actual.get(location, []))
        if expected_ids != actual_ids:
            issues.append(f"Location index mismatch at {location}.")
    return issues


def _canonicalize_obj(value: Any) -> Any:
    """Recursively canonicalize nested objects for deterministic comparison."""
    if isinstance(value, dict):
        return {
            key: _canonicalize_obj(val)
            for key, val in sorted(value.items(), key=lambda item: item[0])
        }
    if isinstance(value, list):
        return [_canonicalize_obj(item) for item in value]
    return value

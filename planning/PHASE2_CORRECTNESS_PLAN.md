# Blossom Phase 2 Plan (Correctness First)

Last updated: 2026-02-20

Implementation status (2026-02-20):

- Stage 2.0 tooling is now in code:
  - `blossom/blossom/simulation/invariants.py`
  - `scripts/benchmark/verify_equivalence.py`
  - `Universe(..., validate_invariants=True)` and CLI flag
- Native intent API landed in core:
  - `blossom/blossom/simulation/intent_api.py`
  - default `(org, ctx)` callback invocation + `@legacy_behavior` escape hatch
  - `CompositeIntent` runtime support in `Organism`
- Stage 2.1 micro-optimizations started:
  - fast-path `Organism.clone` (bypass `__init__` reconstruction)
  - reduced builtin callback normalization overhead
  - `parse_intent` loop micro-optimizations

## 1) Objective

Increase compute throughput while preserving exact simulation semantics.

## 2) Non-Negotiables

- `parse_intent` remains the single conflict-resolution boundary.
- Custom behavior support remains first-class.
- Fixed-seed runs must remain deterministic and equivalent at the state level.
- Refactors must not mutate old-timestep state in place unless explicitly intended.

## 3) Correctness Gates (Must Pass Before/After Each Optimization)

## Gate C1: Step-Level Invariants

Validate every timestep:

- Organism IDs are unique in resolved state.
- `population_dict` statistics match organism list counts.
- `organisms_by_location` matches organism locations exactly.
- Organism locations are in world bounds.
- `world.current_time == universe.current_time`.

## Gate C2: Seeded Equivalence (Canonical Scenarios)

For fixed seeds, baseline vs refactor must match on:

- Final organism states (full canonicalized JSON for small runs).
- Per-step digest (`state_hash`) for short runs.
- Final species statistics for larger runs.

## Gate C3: Seeded Equivalence (Custom Behavior)

Run at least one custom callback scenario (predator-prey style). Match:

- Per-step species counts.
- Final organism IDs + alive/dead outcomes.
- Final world summary fields.

## Gate C4: Resume Equivalence

Compare:

- Continuous run `0..T`
- Run `0..k`, resume, then `k..T`

Final state must match for same seed and config.

## Gate C5: Performance Gate

Only after C1-C4 pass:

- Re-run canonical A/B/C (`n=3`) and update `BENCHMARKS.md`.
- Track compute-only gains (`mean_step_compute_ms`, `timesteps_per_sec`).

## 4) Execution Stages

## Stage 2.0: Build Validation Harness (No Perf Changes)

Deliverables:

- `scripts/benchmark/verify_equivalence.py` to compare two run outputs.
- `state_hash` utility for per-step canonical digests.
- Invariant checker utility callable from the timestep loop in debug mode.
- Callback API proposal and migration notes:
  - `planning/CUSTOM_INTENT_API_PROPOSAL.md`

Exit criteria:

- C1-C4 runnable from CLI and green on current baseline.

## Stage 2.1: Safe Micro-Optimizations (Low Semantic Risk)

Candidate changes:

- Cache/reuse custom module loads (avoid repeated import overhead from cloning).
- Reduce temporary allocations in helper paths.
- Small `parse_intent` data-structure improvements without changing resolution policy.

Exit criteria:

- C1-C4 green.
- Any measurable compute improvement recorded.

## Stage 2.2: Timestep Loop Redundancy Cleanup

Candidate changes:

- Remove or defer duplicate full-structure rebuilds where proven redundant.
- Keep observable behavior identical for custom callbacks.

Important:

- No change merges without seeded equivalence proof on custom scenarios.

Exit criteria:

- C1-C4 green.
- Canonical B compute improvement is significant and stable.

## Stage 2.3: Indexed Access Layer (Object-First)

Candidate changes:

- Introduce maintained indexes as derived caches over object state:
  - `id -> organism`
  - `location -> organisms`
  - `species -> organisms`
- Update via controlled commit path after `parse_intent`.

Exit criteria:

- C1-C4 green.
- Query-heavy custom scenarios show measurable gains.

## Stage 2.4: Optional Advanced Engine Work (Only If Needed)

Potential:

- Compact intent metadata (patch/delta representation) for built-in fast paths.
- Keep object-intent fallback for arbitrary callbacks.

Exit criteria:

- Same correctness gates as above.
- Complexity justified by benchmark gains.

## 5) Stop Conditions

Stop and re-evaluate if:

- Any step-level equivalence diverges without clear, intended semantic change.
- Custom behavior compatibility regresses.
- Additional complexity yields minimal compute gains.

## 6) Immediate Next Actions

1. Implement Stage 2.0 equivalence/invariant harness.
2. Add one predator-prey custom-behavior regression case.
3. Start Stage 2.1 with module-loading/cache and parse-intent micro-optimizations.

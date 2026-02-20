# Blossom Roadmap

Last updated: 2026-02-20

## 1) North Star

Blossom should be:

- Flexible enough for custom organism behaviors (core selling point).
- Fast enough to run meaningful simulations locally without long stalls.
- Storage-efficient enough that normal runs do not create unmanageable disk bloat.
- Extensible toward:
  - RL-driven behavior policies.
  - Nature/nurture dynamics (genotype + environment history -> behavior/traits).

## 2) Current Problems

- Excessive data output volume per run.
- Slow timestep throughput with increasing organism count.

## 3) Non-Negotiables

- Do not break existing custom behavior model.
- Keep deterministic behavior with fixed seeds.
- Keep a clear, simple workflow for users running sample scripts/config projects.

## 4) Success Metrics

Track and report for standard benchmark scenarios:

- `timesteps/sec`
- `seconds/timestep`
- `MB written / 1k timesteps`
- `peak disk used / run`
- `resume correctness` (same outputs when replaying from checkpoints with same seed)

Initial target direction (revise after baseline):

- 5x to 20x lower disk output for default runs.
- 2x+ timestep speedup on I/O-heavy scenarios.
- No regression in custom behavior support.

## 5) Phased Plan

## Phase 0: Baseline and Instrumentation (Week 1)

Goals:

- Add run-level instrumentation for compute time vs write time.
- Add output-size tracking in logs/summary.
- Establish 2-3 canonical benchmark scenarios.

Deliverables:

- Internal timing counters in simulation loop.
- Benchmark harness + baseline numbers captured in `BENCHMARKS.md`.

## Phase 1: Storage and I/O Optimizations (Weeks 1-2)

Goals:

- Reduce data footprint and I/O overhead without changing simulation semantics.

Planned features:

- `snapshot_interval` for full state saves every N steps.
- `checkpoint_interval` for resumable checkpoints.
- `log_interval` for summary-only logging cadence.
- Retention policy (`retain_last_checkpoints`).
- Compact output mode (no pretty JSON indentation).
- Optional compression for snapshot files.

Expected impact:

- Major disk reduction and meaningful runtime gains where I/O dominates.

## Phase 2: Hot-Path Runtime Optimization (Weeks 2-4)

Goals:

- Improve throughput in core simulation loop while preserving behavior.

Focus areas:

- Reduce unnecessary object cloning/copying.
- Reduce repeated hashing/rebuild work in timestep loop.
- Optimize intent conflict resolution workflow.
- Micro-optimize built-in behavior functions.

Expected impact:

- Noticeable speedup in CPU-bound scenarios.

## Phase 3: Hybrid Engine Foundations (Weeks 4-6)

Goals:

- Keep custom callbacks intact while enabling optional accelerated paths.

Approach:

- Introduce species-level optional "batched" interface for built-ins.
- Maintain per-organism callback mode as default-compatible fallback.
- Build compatibility tests across both modes.

Expected impact:

- Better scaling on large populations without sacrificing flexibility.

## Phase 4: RL Hooking (Exploration)

Goals:

- Enable policy inference integration without forcing full RL stack in core.

Approach:

- Define `Policy` interface for per-step action proposals.
- Start with inference-only integration.
- Keep training loops external initially.

## Phase 5: Nature/Nurture Model (Stretch)

Goals:

- Add meaningful inheritance and mutation mechanisms that affect behavior.

Approach:

- Explicit genotype representation per organism.
- Inheritance operators (asexual copy, sexual crossover, mutation).
- Genotype -> phenotype mapping influencing action/metabolism/traits.
- Optional nurture state/history modifying phenotype expression.

## 6) Risks and Mitigations

- Risk: Performance work breaks custom behavior flexibility.
  - Mitigation: Preserve callback mode and add regression tests using custom scripts.
- Risk: Optimization changes simulation semantics.
  - Mitigation: Seeded equivalence tests and scenario diffs.
- Risk: Complexity grows too fast with RL/genetics.
  - Mitigation: Keep strict phase gates; do not start stretch work before Phase 1/2 success.

## 7) Immediate Next Steps

1. Implement Phase 0 instrumentation.
2. Collect baseline metrics for canonical scenarios.
3. Implement Phase 1 output controls and compact writes.
4. Re-benchmark and decide whether next effort goes to I/O or CPU hotspots.


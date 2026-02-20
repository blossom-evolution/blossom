# Blossom Benchmarks

Last updated: 2026-02-20

## 1) Purpose

This file defines reproducible benchmark scenarios and records before/after metrics for performance and storage optimization work.

## 2) Benchmark Rules

- Use fixed seed values.
- Run each scenario at least 3 times; report mean and min/max.
- Record system details (CPU, RAM, Python version, OS).
- Use identical configs except for the feature under test.

## 3) Core Metrics

- `total_runtime_s`
- `timesteps_per_sec`
- `mean_step_compute_ms`
- `mean_step_write_ms`
- `data_written_mb`
- `files_created`
- `peak_run_disk_mb`

## 4) Canonical Scenarios

## Scenario A: Small sanity

- Purpose: quick correctness/perf smoke test.
- Config:
  - 2 species, 100 total organisms (`50 + 50`)
  - 1D world size `50`
  - `500` timesteps
  - Built-ins only: `action=move_only`, `movement=simple_random`
  - `linked_modules=[]` for both species

## Scenario B: Medium reference

- Purpose: day-to-day development benchmark.
- Config:
  - 2 species, 2000 total organisms (`1000 + 1000`)
  - 1D world size `100`
  - `250` timesteps
  - Built-ins only: `action=move_only`, `movement=simple_random`
  - `linked_modules=[]` for both species

## Scenario C: Stress

- Purpose: scaling behavior and bottleneck detection.
- Config:
  - 2 species, 10000 total organisms (`5000 + 5000`)
  - 1D world size `200`
  - `60` timesteps
  - Built-ins only: `action=move_only`, `movement=simple_random`
  - `linked_modules=[]` for both species

## 5) Environment Record Template

```md
Date:
Commit:
Python:
OS:
CPU:
RAM:
Notes:
```

## 6) Results Table Template

```md
| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |
|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|
|      |        |          |        |                 |                   |                      |                    |                 |               |                  |       |
```

## 7) Current Baseline

Status: Canonical A/B/C baseline collected (3 repeats each).

Environment:

- Date: 2026-02-20
- Commit: `eb886e0`
- Python: `3.14.2` (`conda` env: `blossom`)
- OS: `Darwin 25.1.0`
- CPU: `Apple M4 Max`
- RAM: `36 GB`
- Notes:
  - Canonical run script: `scripts/benchmark/run_canonical_baselines.py`
  - Seeds: `301, 302, 303`
  - Artifacts cleaned per repeat; results retained in:
    - `blossom/planning/results/2026-02-20-canonical-baselines.json`

Recorded baselines:

| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |
|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|
| 2026-02-20 | eb886e0 | smoke-1species-200x20 | instrumentation baseline | 0.132646 | 150.777583 | 2.875988 | 3.986571 | 4.910294 | 43 | 4.921576 | t=0..20, 200 organisms, 1D world size 20 |
| 2026-02-20 | eb886e0 | A | canonical baseline | 1.786855 | 280.046497 | 1.417922 | 2.025487 | 59.832669 | 1003 | 60.131729 | pop=100, world=50, t=500, n=3, seeds=[301, 302, 303], tps range=269.105-287.312 |
| 2026-02-20 | eb886e0 | B | canonical baseline | 16.314606 | 15.323988 | 30.614711 | 34.628781 | 588.269293 | 503 | 588.420074 | pop=2000, world=100, t=250, n=3, seeds=[301, 302, 303], tps range=15.247-15.411 |
| 2026-02-20 | eb886e0 | C | canonical baseline | 21.575004 | 2.781957 | 183.775233 | 178.271415 | 713.871992 | 123 | 713.908765 | pop=10000, world=200, t=60, n=3, seeds=[301, 302, 303], tps range=2.711-2.830 |

Phase 1 smoke comparison (same tiny scenario, one run each):

| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |
|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|
| 2026-02-20 | eb886e0 | phase1-smoke-20x7 | default output | 0.006071 | 1152.982348 | 0.271990 | 0.453959 | 0.191795 | 17 | 0.196924 | snapshot/log every step, pretty JSON |
| 2026-02-20 | eb886e0 | phase1-smoke-20x7 | output controls enabled | 0.002485 | 2816.665406 | 0.223865 | 0.445834 | 0.029625 | 7 | 0.031767 | `snapshot_interval=2`, `log_interval=3`, `retain_last_checkpoints=2`, `compact_json_output=true` |

Phase 1 trial on canonical-B shape (single run, exploratory):

| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |
|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|
| 2026-02-20 | eb886e0 | B-like-2000x250 | baseline reference (mean of 3) | 16.314606 | 15.323988 | 30.614711 | 34.628781 | 588.269293 | 503 | 588.420074 | from canonical baseline table |
| 2026-02-20 | eb886e0 | B-like-2000x250 | output controls enabled | 8.141418 | 30.707181 | 29.452908 | 3.112765 | 7.305628 | 36 | 7.320461 | single run, seed=901, `snapshot_interval=10`, `log_interval=10`, `retain_last_checkpoints=5`, `compact_json_output=true`; see `planning/results/2026-02-20-phase1-B-trial.json` |

Immediate action (updated 2026-02-20):

1. Completed: canonical A/B/C with Phase 1 settings (`snapshot_interval=10`, `log_interval=10`, `retain_last_checkpoints=5`, `compact_json_output=true`) at `n=3`.
2. Completed: compared against canonical baseline with matching seeds (`101, 102, 103`).
3. Completed: verified sparse logging metrics path in benchmark summarizer.

Full canonical comparison (n=3, seeds 101/102/103):

| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |
|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|
| 2026-02-20 | eb886e0 | A | canonical baseline | 1.737556 | 287.780798 | 1.377503 | 2.097608 | 59.833717 | 1003 | 60.171076 | pop=100, world=50, t=500, n=3, seeds=[101, 102, 103], snapshot=1, log=1, retain=None, compact=False |
| 2026-02-20 | eb886e0 | A | output controls enabled | 0.791238 | 632.086357 | 1.368826 | 0.213650 | 0.370842 | 61 | 0.397544 | pop=100, world=50, t=500, n=3, seeds=[101, 102, 103], snapshot=10, log=10, retain=5, compact=True |
| 2026-02-20 | eb886e0 | B | canonical baseline | 16.737920 | 14.962178 | 31.177809 | 35.773872 | 588.267094 | 503 | 588.437037 | pop=2000, world=100, t=250, n=3, seeds=[101, 102, 103], snapshot=1, log=1, retain=None, compact=False |
| 2026-02-20 | eb886e0 | B | output controls enabled | 8.459223 | 29.564505 | 30.738224 | 3.098669 | 7.305656 | 36 | 7.320469 | pop=2000, world=100, t=250, n=3, seeds=[101, 102, 103], snapshot=10, log=10, retain=5, compact=True |
| 2026-02-20 | eb886e0 | C | canonical baseline | 20.643009 | 2.907005 | 169.934401 | 174.115743 | 713.870548 | 123 | 713.911967 | pop=10000, world=200, t=60, n=3, seeds=[101, 102, 103], snapshot=1, log=1, retain=None, compact=False |
| 2026-02-20 | eb886e0 | C | output controls enabled | 11.058017 | 5.426046 | 168.909219 | 15.391069 | 36.472356 | 17 | 36.477941 | pop=10000, world=200, t=60, n=3, seeds=[101, 102, 103], snapshot=10, log=10, retain=5, compact=True |

Relative impact (output controls vs baseline):

- Scenario A: runtime `54.46%` faster, throughput `2.196x`, data written `99.38%` lower.
- Scenario B: runtime `49.46%` faster, throughput `1.976x`, data written `98.76%` lower.
- Scenario C: runtime `46.43%` faster, throughput `1.867x`, data written `94.89%` lower.

Artifacts:

- `blossom/planning/results/2026-02-20-canonical-baselines-full/canonical_baseline_results.json`
- `blossom/planning/results/2026-02-20-output-controls-full/canonical_baseline_results.json`

Phase 2 native-intent smoke (single repeat, seed 921):

| Date | Commit | Scenario | Change | total_runtime_s | timesteps_per_sec | mean_step_compute_ms | mean_step_write_ms | data_written_mb | files_created | peak_run_disk_mb | Notes |
|------|--------|----------|--------|----------------:|------------------:|---------------------:|-------------------:|----------------:|--------------:|-----------------:|-------|
| 2026-02-20 | ff975fe | A | output controls enabled | 0.902370 | 554.096382 | 1.576245 | 0.228496 | 0.370864 | 61 | 0.397553 | n=1, seed=921, snapshot=10, log=10, retain=5, compact=True, validate=False |
| 2026-02-20 | ff975fe | B | output controls enabled | 9.538821 | 26.208690 | 34.813639 | 3.341645 | 7.305583 | 36 | 7.320387 | n=1, seed=921, snapshot=10, log=10, retain=5, compact=True, validate=False |
| 2026-02-20 | ff975fe | C | output controls enabled | 12.094985 | 4.960734 | 185.752976 | 15.830112 | 36.471949 | 17 | 36.477533 | n=1, seed=921, snapshot=10, log=10, retain=5, compact=True, validate=False |

Correctness harness smoke:

- Invariant-enabled deterministic A-run equivalence passed:
  - left/right same seed (`911`) with `validate_invariants=true`
  - `verify_equivalence.py` reported:
    - `per_step_equal=true`
    - `final_state_equal=true`
    - `final_species_stats_equal=true`
    - `final_outcomes_equal=true`

## 8) Acceptance Gates by Phase

## Gate for Phase 1 (I/O optimization)

- Demonstrate at least 5x reduction in `data_written_mb` on Scenario B.
- No correctness regression on fixed-seed runs.

## Gate for Phase 2 (runtime optimization)

- Demonstrate at least 2x improvement in `timesteps_per_sec` on Scenario B.
- Maintain or improve Scenario A correctness checks.

## Gate for Phase 3 (hybrid acceleration)

- Show scaling improvement on Scenario C.
- Validate fallback behavior for custom callback mode.

## 9) Tooling

Use the run summarizer to produce benchmark numbers:

```bash
python scripts/benchmark/summarize_run.py --project-dir PATH_TO_PROJECT --format json
```

or a Markdown row:

```bash
python scripts/benchmark/summarize_run.py --project-dir PATH_TO_PROJECT --format md
```

Run canonical baseline scenarios:

```bash
python scripts/benchmark/run_canonical_baselines.py --scenario all --repeats 3 --seed-base 300
```

Verify run equivalence (state hashes + final outcomes):

```bash
python scripts/benchmark/verify_equivalence.py --left-project PATH_A --right-project PATH_B --require-all-steps
```

# Blossom Engineering Decisions

Last updated: 2026-02-20

This file tracks architecture and product decisions in lightweight ADR format.

## ADR-001: Keep Custom Behaviors as First-Class

- Date: 2026-02-20
- Status: Accepted

Context:

- Custom organism behavior is a key differentiator for Blossom.
- Performance work can accidentally push toward rigid internal-only behavior logic.

Decision:

- Preserve callback-based custom behavior support as a core API guarantee.
- Any optimized execution mode must provide a compatibility path for existing custom callbacks.

Consequences:

- Full vectorization of all paths is not realistic as a first move.
- A hybrid design is preferred over an all-or-nothing rewrite.

## ADR-002: Optimize I/O Before Deep Engine Rewrite

- Date: 2026-02-20
- Status: Accepted

Context:

- Current runs write full state every timestep, causing heavy disk usage and significant runtime overhead.

Decision:

- Prioritize output controls and compact serialization before deeper runtime redesign.

Consequences:

- Fast user-visible wins in storage and runtime.
- Better benchmark clarity for later CPU-focused work.

## ADR-003: Adopt a Hybrid Performance Model

- Date: 2026-02-20
- Status: Proposed

Context:

- Some operations are highly vectorizable (metabolism, built-in movement, world updates).
- Arbitrary user callbacks are not uniformly vectorizable.

Decision:

- Build optional accelerated pathways for built-in/batched operations.
- Maintain callback mode for custom behaviors.

Consequences:

- More implementation complexity.
- Better scaling without abandoning flexibility.

## ADR-004: RL Integration as Interface, Not Full Framework

- Date: 2026-02-20
- Status: Proposed

Context:

- RL is interesting but would sharply expand scope if training/runtime are deeply embedded.

Decision:

- Add policy inference hooks first.
- Keep training workflows external until core simulation performance and storage are stable.

Consequences:

- Lower integration risk.
- Clear boundary between sim engine and ML experimentation.

## ADR-005: Nature/Nurture as a Structured Extension

- Date: 2026-02-20
- Status: Proposed

Context:

- DNA/heritability and mutation are highly compelling but can destabilize core if rushed.

Decision:

- Introduce explicit genotype and inheritance operators only after baseline performance milestones are met.
- Add phenotype mapping and nurture effects as opt-in modules.

Consequences:

- Slower path to advanced biology features.
- Cleaner architecture and lower regression risk.

## Decision Template

Use this for new entries:

```md
## ADR-XXX: Title

- Date: YYYY-MM-DD
- Status: Proposed | Accepted | Superseded

Context:
- ...

Decision:
- ...

Consequences:
- ...
```


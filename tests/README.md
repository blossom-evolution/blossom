# Test Suite

Run tests from the `blossom/` directory:

```bash
conda run -n blossom python -m pip install -e ".[test]"
conda run -n blossom pytest
```

Current layout:

- `tests/unit/`: focused unit tests (intent dispatch/materialization).
- `tests/integration/`: deterministic small-run integration checks.
  - Uses pytest `tmp_path`; artifacts are tiny and ephemeral.

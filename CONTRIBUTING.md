# Contributing

This package is the single source of truth for the comprehensive-index contract.
Changes to the schema ripple to the `cyborg` producer and every consumer, so the
gates below are strict by design.

## Setup

The project uses [uv](https://docs.astral.sh/uv/). No manual virtualenv needed:

```bash
uv run --extra dev pytest      # run anything through uv
make all                       # the full gate CI runs
```

`make all` = lint + format-check + typecheck + test + schema-drift gate +
breaking-change gate.

## Changing the schema

1. Edit the models in `src/orgindex_schema/models.py`.
2. Bump `SCHEMA_VERSION` in `src/orgindex_schema/version.py` per
   [COMPATIBILITY.md](COMPATIBILITY.md) (additive → minor, breaking → major).
3. `make schema` to regenerate `index.schema.json`; commit it.
4. `make compat-check` to confirm the version bump matches the detected change
   class. CI runs this too and will block a mismatch.
5. Add a `CHANGELOG.md` entry under `Unreleased`.

A **breaking** change (major) is a coordinated rollout — see the major checklist in
[RELEASING.md](RELEASING.md). Do not merge one without agreeing the producer/consumer
rollout order first.

## Dependencies

- `uv.lock` is committed; if you change dependencies, run `uv lock` and commit it
  (CI runs `uv lock --check`).
- Runtime deps must stay minimal (pydantic only) — this package is depended on by
  both the producer and every consumer, so keep its footprint tiny.
- **Dev tooling (ruff/mypy/pytest) is bumped by hand**, not by Dependabot (it only
  tracks `pydantic` + GitHub Actions). To adopt a newer version, widen the bound in
  `pyproject.toml` *and* run `uv lock` in the same change, then fix any new
  lint/type findings — keeping the cap and the lock in sync.

## Ground rules

- Keep the schema modeling the index **exactly as written to disk** (round-trip
  must hold); query-time types stay in the consumers.
- Match the surrounding style; strict mypy and ruff must pass.
- Reviews/approvals follow `OWNERS`.

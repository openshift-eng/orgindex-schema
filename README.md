# orgindex-schema

Canonical, versioned **pydantic** schema for the organizational-data *comprehensive index*: the on-disk JSON contract produced by the `cyborg` org-indexer and consumed by the `cyborg-data` Go and Python clients (and downstream MCP servers, bots, and web apps).

This package is the single source of truth for the index shape. It is intentionally dependency-light (pydantic only), so both the producer and every consumer can depend on it without pulling in `orglib`.

> **Internal-first.** This is open source (Apache-2.0) and published on PyPI, but it is maintained for internal Red Hat / openshift-eng use and is unlikely to be useful outside that ecosystem. Support is best-effort.

## What it defines

- `ComprehensiveIndexModel` — the top-level `{ metadata, lookups, indexes }` on-disk shape.
- `SCHEMA_VERSION` — the embedded contract version (semver; see `COMPATIBILITY.md`).
- `index.schema.json` — the committed JSON Schema (emitted in **serialization** mode), from which the Go consumer generates its structs.

It models the index **exactly as written to disk** (no normalization), so
`ComprehensiveIndexModel.model_validate(json).model_dump()` round-trips an index unchanged.

Query-result types that are computed at query time and never serialized
(`HierarchyPathEntry`, `OrgInfo`, `HierarchyNode`) are intentionally **out of scope** and stay in the consumers.

## Installation

```bash
pip install "orgindex-schema>=0.1,<0.2"
```

The package is in **initial development (0.x)** — the contract is still settling as
the first consumer is built, so each `0.x` **minor** may break. Pin to a single
minor (`>=0.1,<0.2`); when the shape is proven in a real consumer the project will
cut `1.0.0`, after which you pin to a major range (`>=1,<2`). The package major is
coupled to the contract `SCHEMA_VERSION` major (see
[COMPATIBILITY.md](COMPATIBILITY.md)), so the pin is a resolver-enforced
compatibility check, not just a convention. Hash-pin in your lockfile and resolve
from a single index to avoid dependency-confusion substitution.

## Usage

```python
import json
from orgindex_schema import ComprehensiveIndexModel, SCHEMA_VERSION

with open("comprehensive_index.json") as f:
    index = ComprehensiveIndexModel.model_validate(json.load(f))
```

## Development

Uses [uv](https://docs.astral.sh/uv/); no manual virtualenv needed.

```bash
make all           # the full gate CI runs (lint, format, types, tests, both gates)
make schema        # regenerate index.schema.json from the models
make schema-check  # drift gate: fail if index.schema.json is stale
make compat-check  # breaking-change gate: version bump must match the schema diff
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the schema-change workflow,
[COMPATIBILITY.md](COMPATIBILITY.md) for the versioning policy, and
[RELEASING.md](RELEASING.md) for how releases are cut and published.

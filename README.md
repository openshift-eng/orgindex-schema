# orgindex-schema

Canonical, versioned **pydantic** schema for the organizational-data *comprehensive index*: the on-disk JSON contract produced by the `cyborg` org-indexer and consumed by the `cyborg-data` Go and Python clients (and downstream MCP servers, bots, and web apps).

This package is the single source of truth for the index shape. It is intentionally dependency-light (pydantic only), so both the producer and every consumer can depend on it without pulling in `orglib`.

## What it defines

- `ComprehensiveIndexModel` — the top-level `{ metadata, lookups, indexes }` on-disk shape.
- `SCHEMA_VERSION` — the embedded contract version (semver; see `COMPATIBILITY.md`).
- `index.schema.json` — the committed JSON Schema (emitted in **serialization** mode), from which the Go consumer generates its structs.

It models the index **exactly as written to disk** (no normalization), so
`ComprehensiveIndexModel.model_validate(json).model_dump()` round-trips an index unchanged.

Query-result types that are computed at query time and never serialized
(`HierarchyPathEntry`, `OrgInfo`, `HierarchyNode`) are intentionally **out of scope** and stay in the consumers.

## Usage

```python
import json
from orgindex_schema import ComprehensiveIndexModel, SCHEMA_VERSION

with open("comprehensive_index.json") as f:
    index = ComprehensiveIndexModel.model_validate(json.load(f))
```

## Development

```bash
make schema        # regenerate index.schema.json from the models
make schema-check  # CI drift gate: fail if index.schema.json is stale
make test          # round-trip + collision + optionals tests
make lint typecheck
```

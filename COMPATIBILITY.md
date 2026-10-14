# Compatibility and versioning

`orgindex-schema` carries two version numbers with different jobs:

- **`SCHEMA_VERSION`** (`orgindex_schema.version`, currently `1.0.0`): the version
  of the on-disk index *contract*. The producer embeds it in
  `metadata.schema_version`; consumers check it at load time. This document
  governs this number.
- **Package version** (`pyproject.toml`, currently `0.1.0`): the Python
  distribution version. Consumers pin it by git tag
  (`orgindex-schema @ git+...@v0.1.0`). It is bumped for any release, including
  doc-only ones, and moves independently of `SCHEMA_VERSION`.

## SCHEMA_VERSION semver

The contract version is semver over the *shape of the index JSON*:

- **MAJOR**: a breaking change. A consumer built against the previous major may
  misread the new index. Breaking changes are:
  - removing or renaming a field
  - changing a field's type
  - adding a new *required* field (one without a default)
  - removing an enum value, or tightening a constraint
  - making an optional field required
- **MINOR**: an additive, backward-compatible change, such as a new
  optional/defaulted field or a new enum value a tolerant reader can ignore.
- **PATCH**: documentation or non-structural changes that do not affect the JSON
  shape.

Every field has a default and consumers read with `extra="ignore"`, so a MINOR
bump is invisible to an older consumer: it ignores fields it does not recognize
and defaults fields the producer has not yet started sending. The producer
itself validates strictly (`extra="forbid"`) before writing, so an unmodeled
field is caught at build time rather than shipped.

## Consumer compatibility rule

A consumer compares the `schema_version` in a loaded index against the
`SCHEMA_VERSION` it was built with:

- **Same major**: compatible. Load.
- **Different major**: incompatible. Reject.
- **Absent**: an index predating versioning. Warn (with a sunset date) and load.

The producer begins embedding `schema_version`; the load-time
check in the Go and Python clients follows.

## Changing the schema

1. Edit the models in `src/orgindex_schema/models.py`.
2. Bump `SCHEMA_VERSION` in `src/orgindex_schema/version.py` per the rules above.
3. Run `make schema` to regenerate `index.schema.json` and commit it; the
   `make schema-check` CI gate fails on drift.
4. A MAJOR bump is a deliberate, human-reviewed decision. Coordinate the rollout
   across the producer and every consumer before merging.

An automated breaking-change gate, diffing a proposed schema against the oldest
supported baseline and blocking an un-flagged breaking change, is planned.
Until it exists, the correctness of a version bump is enforced by review.

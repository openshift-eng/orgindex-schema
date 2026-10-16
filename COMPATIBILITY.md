# Compatibility and versioning

`orgindex-schema` carries two version numbers with different jobs:

- **`SCHEMA_VERSION`** (`orgindex_schema.version`, currently `1.0.0`): the version
  of the on-disk index *contract*. The producer embeds it in
  `metadata.schema_version`; consumers check it at load time. This document
  governs this number.
- **Package version** (derived from the git tag by `hatch-vcs`, exposed as
  `orgindex_schema.__version__`): the Python distribution version on PyPI. It is
  bumped for any release, including doc-only ones. Its **major is coupled** to
  `SCHEMA_VERSION`'s major (see below); its minor/patch move independently.

## Package version ↔ SCHEMA_VERSION coupling

The two numbers are distinct but their **majors move together**:

> **The package MAJOR equals `SCHEMA_VERSION`'s major.** A contract break
> (`SCHEMA_VERSION 1.x → 2.0`) ships as a new package major (`→ 2.0.0`).

This makes a consumer's dependency pin a real, resolver-enforced compatibility
check rather than a convention. A consumer that reads a major-1 index pins:

```
orgindex-schema>=1,<2
```

and pip/uv will refuse to install a breaking major — the runtime `schema_version`
check (below) is then defense-in-depth, not the only guard. The release workflow
enforces the coupling: a tag whose major disagrees with `SCHEMA_VERSION`'s major
fails to publish.

Within a major, minor/patch of the package and of `SCHEMA_VERSION` need not match:
a packaging- or docs-only fix bumps the package patch while `SCHEMA_VERSION` holds.

### Initial development (0.x)

**The contract is currently at major `0`.** Per semver, major `0` means the shape is
still in flux while the first consumer is being built, so the normal MAJOR ceremony
is deferred and the bump rules shift down one place:

- **breaking** change → bump the **MINOR** (`0.1.x → 0.2.0`)
- **additive** change → bump the **PATCH** (`0.1.0 → 0.1.1`)
- there is **no cross-major stability promise**; a `0.x` consumer pins to a single
  minor (`orgindex-schema>=0.1,<0.2`).

When the shape is validated by a real consumer, the project cuts **`1.0.0`** — the
deliberate declaration of stability — and the rules above (breaking → MAJOR) take
over. The breaking-change gate applies the `0.x` rules automatically while the major
is `0`.

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

## Automated breaking-change gate

The correctness of a version bump is enforced automatically, not just by review.
`scripts/schema_compat.py` (run by `make compat-check` and in CI) diffs the schema
generated from the current models against the last released baseline in
`schema/baselines/v<major>.json`, classifies the diff as `breaking` / `additive` /
`none` by the rules above, and fails unless `SCHEMA_VERSION` was bumped to match:

- a breaking diff without the required bump fails (MAJOR when stable, MINOR while 0.x);
- an additive diff without at least the required bump fails (MINOR when stable, PATCH while 0.x);
- a version regression fails.

The gate is conservative: an ambiguous change is classified as breaking, so the
failure mode is "asks for a bigger bump," never "lets a break through un-flagged".
Refresh the baseline on release with `make baseline`.

## Support window and deprecation

This policy takes effect at **`1.0.0`**. While the contract is at `0.x` there is no
support window: only the latest `0.x` is supported and breaking changes are expected.

- **Supported majors (from 1.0):** the current major and the previous major (N and
  N-1). Older majors are out of support. On a new major, cut a `release-<old>.x`
  branch so critical and security fixes can be backported to the old contract.
- **Deprecate before removing:** a field slated for removal is first made optional
  and flagged (producer/consumer emit a deprecation warning with a sunset date),
  then removed in the next major — mirroring how an absent `schema_version` is
  warned-and-loaded with a sunset date today.
- **Coordinated rollout:** a major is landed producer-first (it embeds the new
  `schema_version`), then consumers, then the old major is sunset. See
  `RELEASING.md` for the checklist.

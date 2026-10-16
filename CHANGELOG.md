# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project carries **two** version numbers (see [COMPATIBILITY.md](COMPATIBILITY.md)):
the **package** version (this changelog's headings) and the on-disk
**`SCHEMA_VERSION`** contract. Their majors move together. Entries that change the
contract note the `SCHEMA_VERSION` transition and, for a major, link a migration note.

## [Unreleased]

### Added
- Release engineering: tag-driven publishing to PyPI via Trusted Publishing (OIDC),
  with build-provenance attestations; TestPyPI dry runs for pre-release tags.
- Automated **breaking-change gate** (`scripts/schema_compat.py`, `make compat-check`)
  that classifies a schema change against the last released baseline and fails unless
  `SCHEMA_VERSION` was bumped to match.
- `schema/baselines/` released-schema baselines and `make baseline` to refresh them.
- Package version is now derived from the git tag (`hatch-vcs`); `__version__` is
  exposed on the package.
- CI across Python 3.11–3.13; `CONTRIBUTING.md`, `RELEASING.md`, and this
  changelog.

### Changed
- Documented the **support window / deprecation policy** and the package-major ↔
  `SCHEMA_VERSION`-major coupling in `COMPATIBILITY.md`.

## [0.1.0] — unreleased

First published release, in **initial development (0.x)**. `SCHEMA_VERSION` 0.1.0 —
the comprehensive-index contract as produced by the `cyborg` org-indexer and read by
the `cyborg-data` clients. The shape may still change by `0.x` minor as the first
consumer is built; the project will cut `1.0.0` once it is validated in a real
consumer. The package major is coupled to the contract major throughout.

[Unreleased]: https://github.com/openshift-eng/orgindex-schema/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/openshift-eng/orgindex-schema/releases/tag/v0.1.0

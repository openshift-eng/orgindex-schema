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

## [1.0.0] — unreleased

First published release. `SCHEMA_VERSION` 1.0.0 — the comprehensive-index contract
as produced by the `cyborg` org-indexer and read by the `cyborg-data` clients.
The package major is aligned to the contract major from this release onward.

[Unreleased]: https://github.com/openshift-eng/orgindex-schema/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/openshift-eng/orgindex-schema/releases/tag/v1.0.0

# Releasing

Releases are **tag-driven**. Pushing a tag builds, verifies, and publishes; there
is no manual upload step and no stored PyPI token.

## Versioning in one line

The package version comes from the git tag (`hatch-vcs`). Its **major must equal
`SCHEMA_VERSION`'s major** — the release workflow enforces this. See
[COMPATIBILITY.md](COMPATIBILITY.md) for the full policy.

> **Current status: initial development (`0.x`).** The contract is still settling,
> so bumps shift down one place: a **breaking** change bumps the **minor**
> (`0.1 → 0.2`) and an **additive** change bumps the **patch** (`0.1.0 → 0.1.1`).
> There is no cross-major ceremony yet. Cut **`1.0.0`** to declare stability once a
> real consumer has validated the shape; the rules below then apply.

Once stable (`>= 1.0.0`):

- Contract unchanged, packaging/docs only → bump package patch/minor (e.g. `1.0.0 → 1.0.1`).
- Additive contract change → bump `SCHEMA_VERSION` minor **and** the package minor.
- Breaking contract change → bump **both majors** and follow the major checklist below.

## Cutting a normal release

1. Ensure `main` is green: `make all`.
2. Update `CHANGELOG.md` — move `Unreleased` items under the new version.
3. If the contract changed, confirm `SCHEMA_VERSION` was bumped (the
   `compat-check` gate will have blocked the PR otherwise) and that
   `schema/baselines/` is current — run `make baseline` and commit if needed.
4. Tag and push:
   ```bash
   git tag -s -a v1.2.0 -m "v1.2.0"
   git push origin v1.2.0
   ```
5. The `Release` workflow builds, runs the full gate, verifies the version
   coupling, publishes to PyPI (Trusted Publishing + attestations), and creates
   the GitHub Release.

## Pre-release dry run

Tag a pre-release (`v1.2.0rc1`) to publish to **TestPyPI** only. Install from there
to smoke-test before the final tag:

```bash
git tag -s -a v1.2.0rc1 -m "v1.2.0rc1" && git push origin v1.2.0rc1
```

## Cutting a MAJOR (breaking) release

A breaking change is a deliberate, coordinated event — do not burn these steps.

1. **Coordinate first.** The `cyborg` producer embeds the new `schema_version`, and
   every consumer must be ready to accept the new major. Agree the rollout order
   before merging.
2. Bump `SCHEMA_VERSION` to the new major and update the models.
3. Add a migration note to `CHANGELOG.md` under the new major.
4. Refresh the baseline: `make baseline` writes `schema/baselines/v<new-major>.json`.
   Keep the previous major's baseline file for the support window.
5. Cut a `release-<old-major>.x` branch from the last release of the old major so
   critical/security fixes can be backported while `main` moves on.
6. Tag `v<new-major>.0.0` and push.

## One-time setup (maintainers)

- **PyPI Trusted Publisher** (project `orgindex-schema`): add a publisher for
  `openshift-eng/orgindex-schema`, workflow `release.yml`, environment `pypi`.
- Repeat on **TestPyPI** with environment `testpypi`.
- Create the `pypi` and `testpypi` **GitHub Environments**; add required reviewers
  to `pypi` so each production publish is human-approved.
- Protect `main` and `release-*`: require the `CI / checks` jobs to pass.

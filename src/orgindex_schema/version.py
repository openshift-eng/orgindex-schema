"""Canonical schema version for the organizational data comprehensive index.

Versioning policy (see COMPATIBILITY.md):
- MAJOR: a breaking change (field removed/renamed, type changed, a new required
  field, an enum value removed, or a constraint tightened).
- MINOR: an additive, backward-compatible change (a new optional/defaulted field).
- PATCH: documentation or non-structural fixes.

Consumers compare the ``schema_version`` embedded in a loaded index against the
version they were built with and reject an incompatible major.

While the contract is at major ``0`` it is in *initial development*: the shape may
still change as the first consumer is built, so a breaking change bumps the MINOR
and an additive change bumps the PATCH. There is no stability promise until
``1.0.0``; see COMPATIBILITY.md.
"""

from typing import Final

SCHEMA_VERSION: Final = "0.1.0"

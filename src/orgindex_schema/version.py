"""Canonical schema version for the organizational data comprehensive index.

Versioning policy (see COMPATIBILITY.md):
- MAJOR: a breaking change (field removed/renamed, type changed, a new required
  field, an enum value removed, or a constraint tightened).
- MINOR: an additive, backward-compatible change (a new optional/defaulted field).
- PATCH: documentation or non-structural fixes.

Consumers compare the ``schema_version`` embedded in a loaded index against the
version they were built with and reject an incompatible major.
"""

from typing import Final

SCHEMA_VERSION: Final = "1.0.0"

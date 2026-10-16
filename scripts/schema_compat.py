"""Breaking-change gate for the comprehensive-index contract.

This is the automated enforcement that ``COMPATIBILITY.md`` describes: it diffs
the schema generated from the current models against the last *released* baseline,
classifies the diff as ``breaking`` / ``additive`` / ``none`` per the rules in
``COMPATIBILITY.md``, and fails unless ``SCHEMA_VERSION`` was bumped to match.

    breaking  -> requires a MAJOR bump   (consumers on the old major may misread)
    additive  -> requires >= a MINOR bump (new optional/defaulted field, new enum value)
    none      -> any bump (incl. none) is fine

Baselines live in ``schema/baselines/v<major>.json`` and are the committed schema
as of the latest release on each major line. The gate compares against the
highest-major baseline present; a deliberate ``v(N) -> v(N+1)`` break is detected
against the ``vN`` baseline and satisfied by the major bump. Refresh the baseline
on release with ``make baseline``.

Usage:
    python -m scripts.schema_compat                 # auto-select highest baseline
    python scripts/schema_compat.py --baseline schema/baselines/v1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Severity ordering: a diff's overall class is the most severe change in it.
NONE, ADDITIVE, BREAKING = 0, 1, 2
_LABEL = {NONE: "none", ADDITIVE: "additive", BREAKING: "breaking"}

# JSON Schema keywords that make a value *more* restrictive. Adding one (or
# tightening it) is breaking; removing one is additive. The current models use
# none of these, so this path is dormant but guards future constraint creep.
_CONSTRAINT_KEYS = frozenset(
    {
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minItems",
        "maxItems",
        "multipleOf",
    }
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = REPO_ROOT / "schema" / "baselines"


class Change:
    """One classified difference between baseline and current."""

    def __init__(self, severity: int, message: str) -> None:
        self.severity = severity
        self.message = message

    def __str__(self) -> str:
        return f"[{_LABEL[self.severity]}] {self.message}"


def _defs(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    defs: dict[str, dict[str, Any]] = schema.get("$defs", {})
    return defs


def _enum(node: dict[str, Any]) -> set[Any] | None:
    """Return the enum value set of a property node, or ``None`` if it is not an enum."""
    if "enum" in node:
        return set(node["enum"])
    return None


def _constraints(node: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in node.items() if k in _CONSTRAINT_KEYS}


def _type_sig(node: dict[str, Any]) -> str:
    """A canonical, comparable string for a property's *type* shape, ignoring
    defaults/titles/descriptions. Refs collapse to the target name so a field's
    model identity (not its inlined contents) is what is compared."""
    if "$ref" in node:
        return "ref:" + str(node["$ref"]).rsplit("/", 1)[-1]
    if "allOf" in node and len(node["allOf"]) == 1:
        return _type_sig(node["allOf"][0])
    if "anyOf" in node:
        return "anyOf(" + ",".join(sorted(_type_sig(s) for s in node["anyOf"])) + ")"
    if "enum" in node:
        base = node.get("type", "")
        return f"enum<{base}>"  # membership compared separately via _enum()
    node_type = node.get("type")
    if node_type == "array":
        return "array<" + _type_sig(node.get("items", {})) + ">"
    if node_type == "object":
        extra = node.get("additionalProperties")
        if isinstance(extra, dict):
            return "map<" + _type_sig(extra) + ">"
        return "object"
    if node_type is not None:
        return f"type:{node_type}"
    return "any"


def _compare_prop(where: str, old: dict[str, Any], new: dict[str, Any]) -> Change | None:
    """Classify a change to a property that exists on both sides."""
    old_enum, new_enum = _enum(old), _enum(new)
    if old_enum is not None and new_enum is not None and _type_sig(old) == _type_sig(new):
        removed, added = old_enum - new_enum, new_enum - old_enum
        if removed:
            return Change(BREAKING, f"{where}: enum value(s) removed: {sorted(map(str, removed))}")
        if added:
            return Change(ADDITIVE, f"{where}: enum value(s) added: {sorted(map(str, added))}")
        return None

    if _type_sig(old) != _type_sig(new):
        return Change(BREAKING, f"{where}: type changed ({_type_sig(old)} -> {_type_sig(new)})")

    old_c, new_c = _constraints(old), _constraints(new)
    if old_c != new_c:
        tightened = set(new_c) - set(old_c) or any(old_c.get(k) != v for k, v in new_c.items() if k in old_c)
        if tightened:
            return Change(BREAKING, f"{where}: constraint tightened ({old_c} -> {new_c})")
        return Change(ADDITIVE, f"{where}: constraint relaxed ({old_c} -> {new_c})")
    return None


def diff_schemas(baseline: dict[str, Any], current: dict[str, Any]) -> list[Change]:
    """Classified differences from ``baseline`` to ``current`` per COMPATIBILITY.md."""
    changes: list[Change] = []
    base_defs, cur_defs = _defs(baseline), _defs(current)

    for name, base_def in base_defs.items():
        if name not in cur_defs:
            changes.append(Change(BREAKING, f"definition '{name}' removed or renamed"))
            continue
        cur_def = cur_defs[name]
        base_props = base_def.get("properties", {})
        cur_props = cur_def.get("properties", {})
        base_req = set(base_def.get("required", []))
        cur_req = set(cur_def.get("required", []))

        for field, base_node in base_props.items():
            where = f"{name}.{field}"
            if field not in cur_props:
                changes.append(Change(BREAKING, f"{where}: field removed or renamed"))
                continue
            change = _compare_prop(where, base_node, cur_props[field])
            if change is not None:
                changes.append(change)
            if field in cur_req and field not in base_req:
                changes.append(Change(BREAKING, f"{where}: optional field became required"))

        for field in cur_props:
            if field not in base_props:
                where = f"{name}.{field}"
                if field in cur_req:
                    changes.append(Change(BREAKING, f"{where}: new required field (no default)"))
                else:
                    changes.append(Change(ADDITIVE, f"{where}: new optional field"))

    return changes


def _schema_version(schema: dict[str, Any]) -> str:
    """The contract version a schema encodes (Metadata.schema_version's default)."""
    return str(_defs(schema)["Metadata"]["properties"]["schema_version"]["default"])


def _parse_semver(version: str) -> tuple[int, int, int]:
    core = version.split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"not a MAJOR.MINOR.PATCH version: {version!r}")
    major, minor, patch = (int(p) for p in parts)
    return major, minor, patch


def _pick_baseline() -> Path:
    candidates = sorted(BASELINE_DIR.glob("v*.json"))
    if not candidates:
        raise SystemExit(f"no baselines found in {BASELINE_DIR}")
    return max(candidates, key=lambda p: int(p.stem.lstrip("v")))


def check(baseline_path: Path, current: dict[str, Any]) -> int:
    baseline = json.loads(baseline_path.read_text())
    changes = diff_schemas(baseline, current)
    severity = max((c.severity for c in changes), default=NONE)

    base_v = _parse_semver(_schema_version(baseline))
    cur_v = _parse_semver(_schema_version(current))

    try:
        shown_path: Any = baseline_path.relative_to(REPO_ROOT)
    except ValueError:
        shown_path = baseline_path
    print(f"baseline: {shown_path} (SCHEMA_VERSION {_schema_version(baseline)})")
    print(f"current:  SCHEMA_VERSION {_schema_version(current)}")
    print(f"detected change class: {_LABEL[severity]}")
    for c in sorted(changes, key=lambda c: -c.severity):
        print(f"  {c}")

    transition = f"{_schema_version(baseline)} -> {_schema_version(current)}"

    if cur_v < base_v:
        print(f"\nFAIL: SCHEMA_VERSION went backwards ({transition}).")
        return 1

    # Initial development (major 0): the contract is unstable, so a breaking change
    # bumps the MINOR and an additive one the PATCH — no MAJOR ceremony yet.
    if cur_v[0] == 0:
        if severity == BREAKING and cur_v[:2] <= base_v[:2]:
            print(
                f"\nFAIL: breaking change detected but MINOR was not bumped ({transition}).\n"
                f"While the contract is at 0.x, a breaking change requires a MINOR bump "
                f"(0.N -> 0.N+1); see COMPATIBILITY.md."
            )
            return 1
        if severity == ADDITIVE and cur_v <= base_v:
            print(
                f"\nFAIL: additive change detected but no bump ({transition}).\n"
                f"While the contract is at 0.x, an additive change requires at least a PATCH bump."
            )
            return 1
        print("\nOK: SCHEMA_VERSION bump is consistent with the detected change class (0.x initial development).")
        return 0

    # Stable (major >= 1): breaking -> MAJOR, additive -> at least MINOR.
    if severity == BREAKING and cur_v[0] <= base_v[0]:
        print(
            f"\nFAIL: breaking change detected but MAJOR was not bumped ({transition}).\n"
            f"A breaking change requires a new MAJOR and a coordinated rollout (see COMPATIBILITY.md)."
        )
        return 1

    if severity == ADDITIVE and cur_v[:2] <= base_v[:2]:
        print(
            f"\nFAIL: additive change detected but MAJOR.MINOR was not bumped ({transition}).\n"
            f"An additive change requires at least a MINOR bump."
        )
        return 1

    if severity != BREAKING and cur_v[0] > base_v[0]:
        print("\nNOTE: MAJOR was bumped without a detected breaking change. Allowed, but confirm it is intended.")

    print("\nOK: SCHEMA_VERSION bump is consistent with the detected change class.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="baseline schema to compare against (default: highest-major file in schema/baselines/)",
    )
    args = parser.parse_args(argv)

    # Import lazily so --help works without the package installed.
    from orgindex_schema.schema import generate_json_schema

    baseline_path = args.baseline or _pick_baseline()
    return check(baseline_path, generate_json_schema())


if __name__ == "__main__":
    sys.exit(main())

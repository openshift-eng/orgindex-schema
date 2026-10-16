"""Tests for the breaking-change gate (``scripts/schema_compat.py``).

These pin the classification rules from ``COMPATIBILITY.md`` and the version-bump
enforcement, so the gate itself cannot silently regress.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from scripts.schema_compat import ADDITIVE, BREAKING, NONE, check, diff_schemas


def make_schema(version: str, defs: dict[str, Any]) -> dict[str, Any]:
    """A minimal schema carrying a contract version and the given ``$defs``."""
    metadata = {
        "properties": {"schema_version": {"default": version, "type": "string"}},
        "required": [],
    }
    return {"$defs": {"Metadata": metadata, **defs}}


def model(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required or []}


def severity_of(baseline_defs: dict[str, Any], current_defs: dict[str, Any]) -> int:
    changes = diff_schemas(make_schema("1.0.0", baseline_defs), make_schema("1.0.0", current_defs))
    return max((c.severity for c in changes), default=NONE)


def test_identical_schemas_are_none() -> None:
    defs = {"Foo": model({"a": {"type": "string"}})}
    assert severity_of(defs, defs) == NONE


def test_new_optional_field_is_additive() -> None:
    base = {"Foo": model({"a": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}})}
    assert severity_of(base, cur) == ADDITIVE


def test_new_required_field_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}}, required=["b"])}
    assert severity_of(base, cur) == BREAKING


def test_removed_field_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "string"}})}
    assert severity_of(base, cur) == BREAKING


def test_type_change_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "integer"}})}
    assert severity_of(base, cur) == BREAKING


def test_field_becoming_required_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "string"}}, required=["a"])}
    assert severity_of(base, cur) == BREAKING


def test_removed_definition_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string"}}), "Bar": model({"b": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "string"}})}
    assert severity_of(base, cur) == BREAKING


def test_enum_value_added_is_additive() -> None:
    base = {"Foo": model({"a": {"type": "string", "enum": ["x"]}})}
    cur = {"Foo": model({"a": {"type": "string", "enum": ["x", "y"]}})}
    assert severity_of(base, cur) == ADDITIVE


def test_enum_value_removed_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string", "enum": ["x", "y"]}})}
    cur = {"Foo": model({"a": {"type": "string", "enum": ["x"]}})}
    assert severity_of(base, cur) == BREAKING


def test_tightened_constraint_is_breaking() -> None:
    base = {"Foo": model({"a": {"type": "string"}})}
    cur = {"Foo": model({"a": {"type": "string", "maxLength": 10}})}
    assert severity_of(base, cur) == BREAKING


# ---- end-to-end version-bump enforcement via check() ----


def write_baseline(tmp_path: Path, version: str, defs: dict[str, Any]) -> Path:
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(make_schema(version, defs)))
    return path


def test_check_passes_when_breaking_bumps_major(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "1.2.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("2.0.0", {"Foo": model({"a": {"type": "integer"}})})
    assert check(base, current) == 0


def test_check_fails_when_breaking_without_major(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "1.2.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("1.3.0", {"Foo": model({"a": {"type": "integer"}})})
    assert check(base, current) == 1


def test_check_passes_when_additive_bumps_minor(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "1.2.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("1.3.0", {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}})})
    assert check(base, current) == 0


def test_check_fails_when_additive_without_minor(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "1.2.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("1.2.1", {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}})})
    assert check(base, current) == 1


def test_check_fails_on_version_regression(tmp_path: Path) -> None:
    defs = {"Foo": model({"a": {"type": "string"}})}
    base = write_baseline(tmp_path, "1.2.0", defs)
    current = make_schema("1.1.0", defs)
    assert check(base, current) == 1


def test_check_allows_patch_for_no_change(tmp_path: Path) -> None:
    defs = {"Foo": model({"a": {"type": "string"}})}
    base = write_baseline(tmp_path, "1.2.0", defs)
    current = make_schema("1.2.1", defs)
    assert check(base, current) == 0


@pytest.mark.parametrize("bad", ["1.0", "1.0.0.0", "v1.0.0", "abc"])
def test_check_rejects_malformed_version(tmp_path: Path, bad: str) -> None:
    defs = {"Foo": model({"a": {"type": "string"}})}
    base = write_baseline(tmp_path, "1.0.0", defs)
    with pytest.raises(ValueError):
        check(base, make_schema(bad, defs))

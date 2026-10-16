"""Tests for the breaking-change gate (``scripts/schema_compat.py``).

These pin the classification rules from ``COMPATIBILITY.md`` and the version-bump
enforcement, so the gate itself cannot silently regress.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import scripts.schema_compat as sc
from scripts.schema_compat import ADDITIVE, BREAKING, NONE, check, diff_schemas


def make_schema(
    version: str,
    defs: dict[str, Any],
    root_props: dict[str, Any] | None = None,
    root_req: list[str] | None = None,
) -> dict[str, Any]:
    """A minimal schema carrying a contract version and the given ``$defs``.

    ``root_props``/``root_req`` populate the top-level envelope (what pydantic
    emits for the root model outside ``$defs``)."""
    metadata = {
        "properties": {"schema_version": {"default": version, "type": "string"}},
        "required": [],
    }
    schema: dict[str, Any] = {"$defs": {"Metadata": metadata, **defs}}
    if root_props is not None or root_req is not None:
        schema["properties"] = root_props or {}
        schema["required"] = root_req or []
    return schema


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


# ---- 0.x initial-development semantics: breaking -> MINOR, additive -> PATCH ----


def test_check_0x_breaking_requires_minor(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "0.1.0", {"Foo": model({"a": {"type": "string"}})})
    # A breaking change with only a PATCH bump is not enough in 0.x.
    current = make_schema("0.1.1", {"Foo": model({"a": {"type": "integer"}})})
    assert check(base, current) == 1


def test_check_0x_breaking_passes_on_minor(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "0.1.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("0.2.0", {"Foo": model({"a": {"type": "integer"}})})
    assert check(base, current) == 0


def test_check_0x_additive_passes_on_patch(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "0.1.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("0.1.1", {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}})})
    assert check(base, current) == 0


def test_check_0x_additive_requires_a_bump(tmp_path: Path) -> None:
    base = write_baseline(tmp_path, "0.1.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("0.1.0", {"Foo": model({"a": {"type": "string"}, "b": {"type": "string"}})})
    assert check(base, current) == 1


def test_check_promotion_to_1_0_0_is_allowed(tmp_path: Path) -> None:
    # Declaring stability (0.x -> 1.0.0) is allowed even alongside a breaking change.
    base = write_baseline(tmp_path, "0.5.0", {"Foo": model({"a": {"type": "string"}})})
    current = make_schema("1.0.0", {"Foo": model({"a": {"type": "integer"}})})
    assert check(base, current) == 0


# ---- root envelope (the top-level model lives outside $defs) ----


def root_severity(
    base_props: dict[str, Any],
    cur_props: dict[str, Any],
    base_req: list[str] | None = None,
    cur_req: list[str] | None = None,
) -> int:
    base = make_schema("1.0.0", {}, root_props=base_props, root_req=base_req or [])
    cur = make_schema("1.0.0", {}, root_props=cur_props, root_req=cur_req or [])
    return max((c.severity for c in diff_schemas(base, cur)), default=NONE)


def test_root_field_removed_is_breaking() -> None:
    base = {"lookups": {"$ref": "#/$defs/Lookups"}, "metadata": {"$ref": "#/$defs/Metadata"}}
    cur = {"metadata": {"$ref": "#/$defs/Metadata"}}
    assert root_severity(base, cur) == BREAKING


def test_root_field_retyped_is_breaking() -> None:
    base = {"metadata": {"$ref": "#/$defs/Metadata"}}
    cur = {"metadata": {"$ref": "#/$defs/Lookups"}}
    assert root_severity(base, cur) == BREAKING


def test_root_new_required_field_is_breaking() -> None:
    base = {"metadata": {"$ref": "#/$defs/Metadata"}}
    cur = {"metadata": {"$ref": "#/$defs/Metadata"}, "extra": {"type": "string"}}
    assert root_severity(base, cur, cur_req=["extra"]) == BREAKING


def test_root_new_optional_field_is_additive() -> None:
    base = {"metadata": {"$ref": "#/$defs/Metadata"}}
    cur = {"metadata": {"$ref": "#/$defs/Metadata"}, "extra": {"type": "string"}}
    assert root_severity(base, cur) == ADDITIVE


# ---- enums rendered as their own $def, and nullable/union enums ----


def test_standalone_enum_def_value_removed_is_breaking() -> None:
    base = {"Color": {"type": "string", "enum": ["r", "g", "b"]}}
    cur = {"Color": {"type": "string", "enum": ["r", "g"]}}
    assert severity_of(base, cur) == BREAKING


def test_standalone_enum_def_value_added_is_additive() -> None:
    base = {"Color": {"type": "string", "enum": ["r", "g"]}}
    cur = {"Color": {"type": "string", "enum": ["r", "g", "b"]}}
    assert severity_of(base, cur) == ADDITIVE


def test_nullable_enum_value_removed_is_breaking() -> None:
    base = {"Foo": model({"c": {"anyOf": [{"type": "string", "enum": ["x", "y"]}, {"type": "null"}]}})}
    cur = {"Foo": model({"c": {"anyOf": [{"type": "string", "enum": ["x"]}, {"type": "null"}]}})}
    assert severity_of(base, cur) == BREAKING


# ---- required -> optional (relaxation) ----


def test_field_becoming_optional_is_additive() -> None:
    base = {"Foo": model({"a": {"type": "string"}}, required=["a"])}
    cur = {"Foo": model({"a": {"type": "string"}})}
    assert severity_of(base, cur) == ADDITIVE


# ---- const (single-value Literal) and enum<->object kind changes ----


def test_single_value_const_change_is_breaking() -> None:
    # Literal['team'] renders as {"const": "team"}; changing the value is breaking.
    base = {"Foo": model({"kind": {"const": "team", "type": "string"}})}
    cur = {"Foo": model({"kind": {"const": "org", "type": "string"}})}
    assert severity_of(base, cur) == BREAKING


def test_def_kind_change_enum_to_object_is_breaking() -> None:
    base = {"Color": {"type": "string", "enum": ["r", "g"]}}
    cur = {"Color": model({"a": {"type": "string"}})}  # no longer an enum
    assert severity_of(base, cur) == BREAKING


def test_tightened_constraint_on_enum_field_is_breaking() -> None:
    # Membership unchanged, but a new constraint must still be detected.
    base = {"Foo": model({"c": {"type": "string", "enum": ["x", "y"]}})}
    cur = {"Foo": model({"c": {"type": "string", "enum": ["x", "y"], "maxLength": 3}})}
    assert severity_of(base, cur) == BREAKING


# ---- robustness of helpers ----


def test_pick_baseline_ignores_non_major_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sc, "BASELINE_DIR", tmp_path)
    (tmp_path / "v0.json").write_text("{}")
    (tmp_path / "v2.json").write_text("{}")
    (tmp_path / "v.json").write_text("{}")  # stray — must be ignored, not crash
    (tmp_path / "version.json").write_text("{}")  # stray
    assert sc._pick_baseline() == tmp_path / "v2.json"


def test_pick_baseline_errors_when_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sc, "BASELINE_DIR", tmp_path)
    with pytest.raises(SystemExit):
        sc._pick_baseline()


def test_schema_version_missing_default_raises_cleanly() -> None:
    metadata = {"properties": {"schema_version": {"type": "string"}}, "required": ["schema_version"]}
    with pytest.raises(SystemExit):
        sc._schema_version({"$defs": {"Metadata": metadata}})


def test_write_baseline_single_sources_serialization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sc, "BASELINE_DIR", tmp_path)
    assert sc._write_baseline() == 0
    from orgindex_schema import SCHEMA_VERSION

    written = tmp_path / f"v{SCHEMA_VERSION.split('.')[0]}.json"
    assert written.exists()
    assert "Metadata" in json.loads(written.read_text())["$defs"]

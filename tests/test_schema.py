"""The emitted JSON Schema is the artifact the Go consumer is generated from.

These tests pin that it is generated in serialization mode, is structured for
codegen (named ``$defs``, name-keyed maps as ``additionalProperties``), is
deterministic, and that the committed ``index.schema.json`` is not stale.
"""

import json
from pathlib import Path

from orgindex_schema import SCHEMA_VERSION, generate_json_schema

ROOT = Path(__file__).parent.parent


def test_schema_version_is_semver() -> None:
    assert SCHEMA_VERSION.count(".") == 2


def test_schema_top_level_shape() -> None:
    schema = generate_json_schema()
    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"metadata", "lookups", "indexes"}
    assert "$defs" in schema


def test_jira_and_component_ownership_are_bare_maps() -> None:
    """These must codegen to Go ``map[string]...`` (additionalProperties), not a
    wrapper struct."""
    indexes = generate_json_schema()["$defs"]["Indexes"]["properties"]
    assert "additionalProperties" in indexes["jira"]
    assert "additionalProperties" in indexes["component_ownership"]


def test_schema_is_deterministic() -> None:
    a = json.dumps(generate_json_schema(), sort_keys=True)
    b = json.dumps(generate_json_schema(), sort_keys=True)
    assert a == b


def test_committed_schema_is_up_to_date() -> None:
    """In-process drift gate: the committed schema must equal the generated one.
    Run ``make schema`` to refresh it."""
    committed = json.loads((ROOT / "index.schema.json").read_text())
    assert committed == generate_json_schema()

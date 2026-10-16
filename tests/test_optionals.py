"""Optional / environment-dependent fields and on-disk quirks.

``stable_id``/``parent_id`` appear only when the indexer runs with an identity
map; ``group`` can be absent; ``keywords`` can be null; the nested
``component.parent`` is a file-path string (unlike the top-level parent edge);
and ``jira`` uses the literal ``"_project_level"`` key. None of these must be
required, and none must be lost on round-trip.
"""

from orgindex_schema import SCHEMA_VERSION, ComprehensiveIndexModel, ParentRef


def _m(data: dict) -> ComprehensiveIndexModel:
    return ComprehensiveIndexModel.model_validate(data)


def test_stable_id_present_and_absent() -> None:
    data = {
        "lookups": {
            "teams": {
                "WithId": {
                    "name": "WithId",
                    "parent": {"name": "P", "type": "team_group"},
                    "parent_id": "sid-p",
                    "stable_id": "sid-w",
                    "group": {"type": {"name": "team"}},
                },
                "NoId": {"name": "NoId", "group": {"type": {"name": "team"}}},
            }
        }
    }
    model = _m(data)
    with_id = model.lookups.teams["WithId"]
    no_id = model.lookups.teams["NoId"]

    assert with_id.stable_id == "sid-w" and with_id.parent_id == "sid-p"
    assert isinstance(with_id.parent, ParentRef) and with_id.parent.type == "team_group"
    # absent on-disk -> defaults, and omitted from an exclude_unset dump
    assert no_id.stable_id == "" and no_id.parent_id == "" and no_id.parent is None

    dump = model.model_dump(exclude_unset=True)
    assert "stable_id" not in dump["lookups"]["teams"]["NoId"]
    assert "parent_id" not in dump["lookups"]["teams"]["NoId"]
    assert "parent" not in dump["lookups"]["teams"]["NoId"]


def test_group_can_be_null() -> None:
    model = _m({"lookups": {"orgs": {"O": {"name": "O", "group": None}}}})
    assert model.lookups.orgs["O"].group is None


def test_keywords_nullable() -> None:
    data = {"lookups": {"team_groups": {"G": {"name": "G", "group": {"keywords": None}}}}}
    model = _m(data)
    assert model.lookups.team_groups["G"].group is not None
    assert model.lookups.team_groups["G"].group.keywords is None
    assert model.model_dump(exclude_unset=True)["lookups"]["team_groups"]["G"]["group"]["keywords"] is None


def test_component_nested_parent_is_path_string() -> None:
    data = {
        "lookups": {
            "components": {
                "C": {
                    "name": "C",
                    "parent": {"name": "Owner", "type": "team"},
                    "component": {
                        "parent": "/org/config/.../c.yaml",
                        "related_components": [{"component_path": "/org/config/.../d.yaml", "types": ["bugs"]}],
                    },
                }
            }
        }
    }
    comp = _m(data).lookups.components["C"]
    assert isinstance(comp.parent, ParentRef) and comp.parent.name == "Owner"
    assert comp.component is not None
    assert comp.component.parent == "/org/config/.../c.yaml"
    assert comp.component.related_components[0].component_path == "/org/config/.../d.yaml"


def test_jira_project_level_bare_map() -> None:
    data = {"indexes": {"jira": {"AP": {"_project_level": [{"name": "X", "type": "team"}]}}}}
    model = _m(data)
    assert model.indexes.jira["AP"]["_project_level"][0].name == "X"


def test_metadata_without_schema_version_roundtrips() -> None:
    data = {"metadata": {"data_version": "v", "generated_at": "t", "total_employees": 5}}
    model = _m(data)
    # in-process the default is available ...
    assert model.metadata.schema_version == SCHEMA_VERSION
    # ... but an older index that omitted it stays omitted on round-trip
    assert "schema_version" not in model.model_dump(exclude_unset=True)["metadata"]

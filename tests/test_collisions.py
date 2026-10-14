"""The name-collision class of bug: the same name used across
hierarchy types must not clobber. Because each type is its own name-keyed map,
a team and a team_group can share a name and stay distinct."""

from orgindex_schema import ComprehensiveIndexModel


def test_same_name_across_team_and_team_group(sample_data: dict) -> None:
    model = ComprehensiveIndexModel.model_validate(sample_data)

    assert "Application Platform" in model.lookups.teams
    assert "Application Platform" in model.lookups.team_groups

    team = model.lookups.teams["Application Platform"]
    team_group = model.lookups.team_groups["Application Platform"]

    assert team.group is not None and team.group.type is not None
    assert team_group.group is not None and team_group.group.type is not None
    assert team.group.type.name == "team"
    assert team_group.group.type.name == "team_group"
    assert team.description != team_group.description


def test_collision_entities_have_distinct_stable_ids() -> None:
    data = {
        "lookups": {
            "teams": {"Shared": {"name": "Shared", "stable_id": "sid-team", "group": {"type": {"name": "team"}}}},
            "team_groups": {
                "Shared": {"name": "Shared", "stable_id": "sid-tg", "group": {"type": {"name": "team_group"}}}
            },
        }
    }
    model = ComprehensiveIndexModel.model_validate(data)
    assert model.lookups.teams["Shared"].stable_id == "sid-team"
    assert model.lookups.team_groups["Shared"].stable_id == "sid-tg"

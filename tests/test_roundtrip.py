"""Round-trip fidelity: model_validate -> model_dump(exclude_unset) == input.

A mismatch means the schema either dropped a field present on disk (model too
narrow) or coerced a value, i.e. it is not a faithful mirror of the index.
"""

import json
import os
from pathlib import Path

import pytest

from orgindex_schema import ComprehensiveIndexModel


def roundtrip(data: dict) -> dict:
    return ComprehensiveIndexModel.model_validate(data).model_dump(exclude_unset=True)


def test_sample_index_roundtrips(sample_data: dict) -> None:
    assert roundtrip(sample_data) == sample_data


def test_pii_free_shape_roundtrips() -> None:
    """A PII-free index empties employees/mappings/membership and redacts
    escalation, but otherwise keeps the structure."""
    data = {
        "metadata": {"pii_free": True, "total_employees": 0, "total_orgs": 1},
        "lookups": {
            "employees": {},
            "teams": {
                "AP": {
                    "name": "AP",
                    "group": {
                        "type": {"name": "team", "visualize": True},
                        "resolved_people_uid_list": [],
                        "resolved_roles": [],
                        "escalation": [{"name": "[REDACTED]", "url": "", "description": "[REDACTED]"}],
                    },
                }
            },
        },
        "indexes": {
            "membership": {"membership_index": {}},
            "slack_id_mappings": {"slack_uid_to_uid": {}},
            "github_id_mappings": {"github_id_to_uid": {}},
        },
    }
    assert roundtrip(data) == data


@pytest.mark.skipif(
    not os.environ.get("ORGINDEX_SAMPLE_INDEX"),
    reason="set ORGINDEX_SAMPLE_INDEX to a real produced index to round-trip it",
)
def test_real_index_roundtrips() -> None:
    data = json.loads(Path(os.environ["ORGINDEX_SAMPLE_INDEX"]).read_text())
    assert roundtrip(data) == data

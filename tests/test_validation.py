"""conformance_problems: the producer's strict validate-on-write gate."""

import copy

from orgindex_schema import conformance_problems


def test_conforming_sample_has_no_problems(sample_data: dict) -> None:
    assert conformance_problems(sample_data) == []


def test_extra_field_on_entity_is_flagged(sample_data: dict) -> None:
    data = copy.deepcopy(sample_data)
    data["lookups"]["teams"]["Application Platform"]["bogus_field"] = "x"
    problems = conformance_problems(data)
    assert any("bogus_field" in p for p in problems)


def test_swallowed_builder_error_is_flagged(sample_data: dict) -> None:
    """A builder that failed writes ``indexes.<name> = {"error": ...}``, which is
    an unexpected index key and must fail the gate."""
    data = copy.deepcopy(sample_data)
    data["indexes"]["employee"] = {"error": "boom"}
    problems = conformance_problems(data)
    assert any(p.startswith("indexes.employee") for p in problems)


def test_wrong_scalar_type_is_flagged(sample_data: dict) -> None:
    data = copy.deepcopy(sample_data)
    data["metadata"]["total_orgs"] = "five"  # strict: no str -> int coercion
    problems = conformance_problems(data)
    assert any("total_orgs" in p for p in problems)


def test_wrong_container_type_is_flagged(sample_data: dict) -> None:
    data = copy.deepcopy(sample_data)
    data["lookups"]["teams"]["Application Platform"]["group"]["jiras"] = "not-a-list"
    problems = conformance_problems(data)
    assert any("jiras" in p for p in problems)


def test_null_inheritance_is_flagged(sample_data: dict) -> None:
    """inheritance is a string-only enum; a null (a producer/data bug that would
    also break the string-typed consumer) must be caught, not shipped. A live
    generate transiently produced a non-string inheritance and the gate blocked it."""
    data = copy.deepcopy(sample_data)
    data["lookups"]["teams"]["Application Platform"]["group"]["context"][0]["inheritance"] = None
    problems = conformance_problems(data)
    assert any("inheritance" in p for p in problems)


def test_missing_field_is_not_a_problem() -> None:
    """All-optional schema: an index omitting a field (older minor version) still conforms."""
    assert conformance_problems({"metadata": {"data_version": "v"}}) == []

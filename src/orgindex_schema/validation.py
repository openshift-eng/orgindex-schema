"""Strict conformance checking against the canonical index schema.

The producer uses :func:`conformance_problems` as a hard gate before writing or
uploading an index: a non-empty result means the built index does
not conform to the contract and must not ship.

Two classes of problem are detected:

1. **Type / structure violations** via pydantic *strict* validation (no coercion),
   e.g. a string where a list is expected, or ``total_orgs`` emitted as a string.
2. **Unmodeled / extra fields** present in the data but absent from the contract.
   The models read tolerantly (``extra="ignore"``) so they would silently drop
   these; the gate surfaces them instead. This also catches a swallowed builder
   error (``indexes.<name> = {"error": ...}``), which appears as an unexpected key.

Missing fields are intentionally **not** problems: the schema is all-optional for
backward compatibility, so an older index that omits a newer field still conforms.
"""

from typing import Any

from pydantic import ValidationError

from .models import ComprehensiveIndexModel


def _unmodeled_field_paths(model_out: Any, data_in: Any, path: str = "") -> list[str]:
    """Paths present in ``data_in`` but absent from the model's output, i.e. fields
    not defined by the contract (a tolerant reader silently drops these). This also
    catches a swallowed builder error (``indexes.<name> = {"error": ...}``)."""
    out: list[str] = []
    if isinstance(data_in, dict) and isinstance(model_out, dict):
        for key, value in data_in.items():
            child = f"{path}.{key}" if path else key
            if key not in model_out:
                out.append(child)
            else:
                out.extend(_unmodeled_field_paths(model_out[key], value, child))
    elif isinstance(data_in, list) and isinstance(model_out, list):
        for index, (left, right) in enumerate(zip(model_out, data_in, strict=False)):
            out.extend(_unmodeled_field_paths(left, right, f"{path}[{index}]"))
    return out


def conformance_problems(data: dict[str, Any]) -> list[str]:
    """Return human-readable conformance problems; an empty list means ``data``
    conforms to the canonical index schema.

    Validation is non-strict, matching how consumers read the index: the gate
    blocks exactly what a consumer could not load (wrong types, null where a value
    is required, bad containers) and nothing a consumer tolerates. It then reports
    any field present on disk but outside the contract (unmodeled / a swallowed
    builder error). Benign coercions a consumer would apply identically are not
    flagged; missing fields are fine (the schema is all-optional).
    """
    try:
        model = ComprehensiveIndexModel.model_validate(data)
    except ValidationError as exc:
        return [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()]
    return [f"{path}: not part of the index schema" for path in _unmodeled_field_paths(model.model_dump(), data)]

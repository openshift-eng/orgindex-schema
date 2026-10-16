"""Emit the canonical JSON Schema for the comprehensive index.

The schema is generated in **serialization** mode, i.e. it describes the shape as
written to disk / read by consumers (what the Go structs are generated from),
not pydantic's input-validation shape.

To regenerate the committed ``index.schema.json``:

    python -m orgindex_schema > index.schema.json
"""

import json
from typing import Any

from .models import ComprehensiveIndexModel


def generate_json_schema() -> dict[str, Any]:
    """Return the canonical JSON Schema (serialization mode) for the index."""
    return ComprehensiveIndexModel.model_json_schema(mode="serialization")


def dumps_canonical(schema: dict[str, Any]) -> str:
    """Canonical, stable, diff-friendly serialization of a schema dict.

    The single source of truth for how ``index.schema.json`` and the committed
    baselines are written, so the two artifacts never diverge in formatting."""
    return json.dumps(schema, indent=2, sort_keys=True)

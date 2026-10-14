"""Emit the canonical JSON Schema for the comprehensive index.

The schema is generated in **serialization** mode, i.e. it describes the shape as
written to disk / read by consumers (what the Go structs are generated from),
not pydantic's input-validation shape.

To regenerate the committed ``index.schema.json``:

    python -m orgindex_schema > index.schema.json
"""

from typing import Any

from .models import ComprehensiveIndexModel


def generate_json_schema() -> dict[str, Any]:
    """Return the canonical JSON Schema (serialization mode) for the index."""
    return ComprehensiveIndexModel.model_json_schema(mode="serialization")

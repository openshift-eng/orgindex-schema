.PHONY: schema schema-check compat-check baseline test lint format format-check typecheck all

SCHEMA ?= index.schema.json
RUN ?= uv run --extra dev

# Emit the canonical JSON Schema from the pydantic models (serialization mode).
schema:
	$(RUN) python -m orgindex_schema > $(SCHEMA)

# CI drift gate: regenerate and fail if the committed schema is stale.
schema-check:
	$(RUN) python -m orgindex_schema > .schema.generated.json
	diff -u $(SCHEMA) .schema.generated.json && echo "index.schema.json is up to date" || (echo "index.schema.json is STALE: run 'make schema'"; rm -f .schema.generated.json; exit 1)
	@rm -f .schema.generated.json

# Breaking-change gate: classify the current schema against the last released
# baseline and fail unless SCHEMA_VERSION was bumped to match (see COMPATIBILITY.md).
compat-check:
	$(RUN) python scripts/schema_compat.py

# Refresh the released baseline for the current SCHEMA_VERSION major. Run this as
# part of cutting a release, then commit schema/baselines/v<major>.json.
baseline:
	$(RUN) python -c "import json, pathlib; from orgindex_schema import SCHEMA_VERSION; from orgindex_schema.schema import generate_json_schema; major = SCHEMA_VERSION.split('.')[0]; p = pathlib.Path('schema/baselines') / f'v{major}.json'; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(generate_json_schema(), indent=2, sort_keys=True) + '\n'); print(f'wrote {p}')"

test:
	$(RUN) pytest

lint:
	$(RUN) ruff check .

format:
	$(RUN) ruff format .

format-check:
	$(RUN) ruff format --check .

typecheck:
	$(RUN) mypy

all: lint format-check typecheck test schema-check compat-check

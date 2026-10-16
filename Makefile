.PHONY: schema schema-check compat-check baseline test lint format format-check typecheck all

SCHEMA ?= index.schema.json
# RUN wraps every command; PYTHON is the interpreter. Defaults run through uv for
# local dev. In an environment without uv (e.g. the Prow test image, where deps are
# pip-installed), call e.g. `make all RUN= PYTHON=python3.12`.
RUN ?= uv run --extra dev
PYTHON ?= python

# Emit the canonical JSON Schema from the pydantic models (serialization mode).
schema:
	$(RUN) $(PYTHON) -m orgindex_schema > $(SCHEMA)

# CI drift gate: regenerate and fail if the committed schema is stale.
schema-check:
	$(RUN) $(PYTHON) -m orgindex_schema > .schema.generated.json
	diff -u $(SCHEMA) .schema.generated.json && echo "index.schema.json is up to date" || (echo "index.schema.json is STALE: run 'make schema'"; rm -f .schema.generated.json; exit 1)
	@rm -f .schema.generated.json

# Breaking-change gate: classify the current schema against the last released
# baseline and fail unless SCHEMA_VERSION was bumped to match (see COMPATIBILITY.md).
compat-check:
	$(RUN) $(PYTHON) scripts/schema_compat.py

# Refresh the released baseline for the current SCHEMA_VERSION major. Run this as
# part of cutting a release, then commit schema/baselines/v<major>.json. Do NOT run
# it in the same change as a schema edit, or compat-check compares the change
# against itself (see RELEASING.md).
baseline:
	$(RUN) $(PYTHON) scripts/schema_compat.py --write-baseline

# Tools are invoked as `python -m <tool>` so they work without the console scripts
# being on PATH (e.g. in the Prow test image).
test:
	$(RUN) $(PYTHON) -m pytest

lint:
	$(RUN) $(PYTHON) -m ruff check .

format:
	$(RUN) $(PYTHON) -m ruff format .

format-check:
	$(RUN) $(PYTHON) -m ruff format --check .

typecheck:
	$(RUN) $(PYTHON) -m mypy

all: lint format-check typecheck test schema-check compat-check

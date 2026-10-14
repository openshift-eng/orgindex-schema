.PHONY: schema schema-check test lint format format-check typecheck all

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

all: lint format-check typecheck test schema-check

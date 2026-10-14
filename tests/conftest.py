import json
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture
def sample_data() -> dict:
    """The committed representative index sample (synthetic, no real PII)."""
    return json.loads((DATA / "sample_index.json").read_text())

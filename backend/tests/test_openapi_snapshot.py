"""Fail if the live OpenAPI schema drifts from the committed snapshot.

The frontend generates its TypeScript client from backend/openapi.json, so the
schema is a product in itself. Intentional changes: regenerate with
`python -m scripts.export_openapi` and commit the diff (visible in review).
"""

import json
from pathlib import Path

from app.main import app

SNAPSHOT = Path(__file__).resolve().parent.parent / "openapi.json"


def test_openapi_matches_snapshot() -> None:
    live = json.loads(json.dumps(app.openapi()))  # normalise tuples->lists
    committed = json.loads(SNAPSHOT.read_text())
    assert live == committed, (
        "OpenAPI schema drifted from backend/openapi.json. "
        "Run `python -m scripts.export_openapi` and commit the change."
    )

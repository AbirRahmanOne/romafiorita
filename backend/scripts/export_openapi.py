"""Dump the FastAPI OpenAPI schema to backend/openapi.json.

Source for the frontend TypeScript client. Run (from backend/):
  python -m scripts.export_openapi
Then generate types in the frontend, e.g.:
  npx openapi-typescript ../backend/openapi.json -o src/lib/api-types.ts
"""

import json
from pathlib import Path

from app.main import app


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "openapi.json"
    out.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

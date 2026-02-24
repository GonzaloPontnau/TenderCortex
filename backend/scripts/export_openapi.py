"""Export the OpenAPI spec from the FastAPI application to openapi.json.

Usage:
    python backend/scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

# Ensure backend directory is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app  # noqa: E402


def main() -> None:
    spec = app.openapi()
    output_path = backend_dir / "openapi.json"
    output_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(f"OpenAPI spec exported to {output_path}")


if __name__ == "__main__":
    main()

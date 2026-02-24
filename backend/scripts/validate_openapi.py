"""Validate the committed openapi.json against the OpenAPI 3.1 specification.

Usage:
    python backend/scripts/validate_openapi.py
"""

import json
import sys
from pathlib import Path

try:
    from openapi_spec_validator import validate_spec
except ImportError:
    print("ERROR: openapi-spec-validator not installed.")
    print("Install with: pip install openapi-spec-validator>=0.7.0")
    sys.exit(1)


def main() -> None:
    spec_path = Path(__file__).resolve().parent.parent / "openapi.json"

    if not spec_path.exists():
        print(f"ERROR: {spec_path} not found.")
        print("Run 'python backend/scripts/export_openapi.py' first.")
        sys.exit(1)

    spec = json.loads(spec_path.read_text())

    try:
        validate_spec(spec)
        print(f"OK: {spec_path} is a valid OpenAPI spec.")
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

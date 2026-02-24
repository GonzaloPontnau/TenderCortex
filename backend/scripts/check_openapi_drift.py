"""Check that the committed openapi.json matches the runtime spec.

Fails if the committed file is out of date (drift detected).

Usage:
    python backend/scripts/check_openapi_drift.py
"""

import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app  # noqa: E402


def main() -> None:
    spec_path = backend_dir / "openapi.json"

    if not spec_path.exists():
        print(f"ERROR: {spec_path} not found.")
        print("Run 'python backend/scripts/export_openapi.py' first.")
        sys.exit(1)

    committed = json.loads(spec_path.read_text())
    runtime = app.openapi()

    committed_str = json.dumps(committed, indent=2, sort_keys=True)
    runtime_str = json.dumps(runtime, indent=2, sort_keys=True)

    if committed_str != runtime_str:
        print("DRIFT DETECTED: openapi.json does not match the runtime spec.")
        print("Run 'python backend/scripts/export_openapi.py' and commit the result.")
        sys.exit(1)

    print("OK: openapi.json is in sync with the runtime spec.")


if __name__ == "__main__":
    main()

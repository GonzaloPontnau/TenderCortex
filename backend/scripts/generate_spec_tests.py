"""Generate pytest test stubs from SPEC.md files.

Reads SPEC_*.md files and generates skeleton test files with
@pytest.mark.spec for any behaviors documented in the spec.

Usage:
    python backend/scripts/generate_spec_tests.py
"""

import re
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
app_dir = backend_dir / "app"
tests_dir = backend_dir / "tests"


def extract_behaviors(spec_path: Path) -> list[str]:
    """Extract behavior descriptions from a SPEC.md file."""
    content = spec_path.read_text(encoding="utf-8")
    behaviors = []

    # Extract from ## Behavior Specification section
    in_behavior = False
    for line in content.split("\n"):
        if "## Behavior Specification" in line:
            in_behavior = True
            continue
        if in_behavior and line.startswith("## ") and "Behavior" not in line:
            in_behavior = False
            continue
        if in_behavior and line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.")):
            behavior = line.strip().lstrip("0123456789. ")
            if behavior:
                behaviors.append(behavior)

    # Extract from error cases table
    in_errors = False
    for line in content.split("\n"):
        if "### Error Cases" in line or "## Error Cases" in line:
            in_errors = True
            continue
        if in_errors and line.startswith(("#", "## ")):
            in_errors = False
            continue
        if in_errors and "|" in line and "---" not in line and "Error" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2 and parts[0] and not parts[0].startswith("Error"):
                behaviors.append(f"Error: {parts[0]}")

    return behaviors


def behavior_to_test_name(behavior: str) -> str:
    """Convert a behavior description to a test function name."""
    name = behavior.lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return f"test_{name[:60]}"


def generate_test_file(spec_path: Path, behaviors: list[str]) -> str:
    """Generate a pytest test file from behaviors."""
    module_name = spec_path.stem.replace("SPEC_", "")
    lines = [
        f'"""Spec-driven tests for {module_name} (auto-generated from {spec_path.name}).',
        "",
        "These are test stubs. Implement the test body for each behavior.",
        '"""',
        "",
        "import pytest",
        "",
        "",
    ]

    for behavior in behaviors:
        test_name = behavior_to_test_name(behavior)
        lines.extend([
            f"@pytest.mark.spec",
            f'async def {test_name}():',
            f'    """{behavior}"""',
            f"    pytest.skip('Not implemented yet')",
            "",
            "",
        ])

    return "\n".join(lines)


def main() -> None:
    spec_dirs = [
        app_dir / "agents" / "nodes",
        app_dir / "services",
    ]

    generated = 0

    for spec_dir in spec_dirs:
        if not spec_dir.exists():
            continue

        for spec_file in spec_dir.glob("SPEC_*.md"):
            behaviors = extract_behaviors(spec_file)
            if not behaviors:
                print(f"  No behaviors found in {spec_file.name}")
                continue

            module_name = spec_file.stem.replace("SPEC_", "")

            # Determine output directory
            if "nodes" in str(spec_dir):
                output_dir = tests_dir / "unit" / "spec"
            else:
                output_dir = tests_dir / "unit" / "spec"

            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"test_spec_{module_name}.py"

            if output_file.exists():
                print(f"  SKIP (exists): {output_file.relative_to(backend_dir)}")
                continue

            content = generate_test_file(spec_file, behaviors)
            output_file.write_text(content, encoding="utf-8")
            print(f"  GENERATED: {output_file.relative_to(backend_dir)} ({len(behaviors)} behaviors)")
            generated += 1

    print(f"\nGenerated {generated} test file(s).")


if __name__ == "__main__":
    main()

"""Verify spec consistency across the TenderCortex codebase.

Checks:
1. Every node in agents/nodes/ has a SPEC_*.md
2. Every skill in skills/*/ has SKILL.md + definition.py
3. Every service in services/ has a SPEC_*.md
4. (Future) Public interface signatures in specs match actual code

Usage:
    python backend/scripts/check_specs.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
app_dir = backend_dir / "app"
skills_dir = backend_dir / "skills"

errors: list[str] = []
warnings: list[str] = []


def check_node_specs() -> None:
    """Verify every graph node has a corresponding SPEC_*.md."""
    nodes_dir = app_dir / "agents" / "nodes"
    if not nodes_dir.exists():
        errors.append(f"Nodes directory not found: {nodes_dir}")
        return

    node_files = [
        f for f in nodes_dir.iterdir()
        if f.suffix == ".py" and f.name != "__init__.py"
    ]

    spec_files = {f.stem.replace("SPEC_", ""): f for f in nodes_dir.iterdir() if f.name.startswith("SPEC_")}

    for node_file in node_files:
        node_name = node_file.stem
        # Try to find a matching spec (exact or partial match)
        matched = any(
            node_name in spec_name or spec_name in node_name
            for spec_name in spec_files
        )
        if not matched:
            errors.append(f"Missing spec for node: {node_file.name} (expected SPEC_*.md in {nodes_dir})")


def check_skill_specs() -> None:
    """Verify every skill has SKILL.md and definition.py."""
    if not skills_dir.exists():
        warnings.append(f"Skills directory not found: {skills_dir}")
        return

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
            continue

        skill_md = skill_dir / "SKILL.md"
        definition_py = skill_dir / "definition.py"

        if not skill_md.exists():
            errors.append(f"Missing SKILL.md for skill: {skill_dir.name}")
        if not definition_py.exists():
            errors.append(f"Missing definition.py for skill: {skill_dir.name}")


def check_service_specs() -> None:
    """Verify every service has a corresponding SPEC_*.md."""
    services_dir = app_dir / "services"
    if not services_dir.exists():
        errors.append(f"Services directory not found: {services_dir}")
        return

    service_files = [
        f for f in services_dir.iterdir()
        if f.suffix == ".py" and f.name != "__init__.py"
    ]

    spec_files = {f.stem.replace("SPEC_", ""): f for f in services_dir.iterdir() if f.name.startswith("SPEC_")}

    for service_file in service_files:
        service_name = service_file.stem
        matched = any(
            service_name in spec_name or spec_name in service_name
            for spec_name in spec_files
        )
        if not matched:
            errors.append(f"Missing spec for service: {service_file.name} (expected SPEC_*.md in {services_dir})")


def main() -> None:
    print("Checking spec consistency...\n")

    check_node_specs()
    check_skill_specs()
    check_service_specs()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [WARN] {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  [ERROR] {e}")
        print(f"\n{len(errors)} spec consistency error(s) found.")
        sys.exit(1)
    else:
        print("OK: All spec consistency checks passed.")


if __name__ == "__main__":
    main()



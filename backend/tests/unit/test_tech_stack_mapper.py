import sys
from pathlib import Path

import pytest

backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from skills.tech_stack_mapper.impl import extract_tech_stack
from skills.tech_stack_mapper.definition import (
    EmptyInputError,
    RequirementLevel,
)


class TestTechStackMapper:

    def test_extracts_and_normalizes_technologies(self):
        result = extract_tech_stack(
            "We require Python 3.11, PostgreSQL, and React."
        )

        names = {entity.canonical_name for entity in result.entities}

        assert "Python" in names
        assert "PostgreSQL" in names
        assert "React" in names

    def test_extracts_version_constraint(self):
        result = extract_tech_stack(
            "The backend must use Python 3.11."
        )

        python = next(
            entity
            for entity in result.entities
            if entity.canonical_name == "Python"
        )

        assert python.version_constraint == "3.11"

    def test_detects_mandatory_requirement(self):
        result = extract_tech_stack(
            "The system must use PostgreSQL."
        )

        postgres = next(
            entity
            for entity in result.entities
            if entity.canonical_name == "PostgreSQL"
        )

        assert postgres.requirement_level == RequirementLevel.MANDATORY

    def test_detects_nice_to_have_requirement(self):
        result = extract_tech_stack(
            "React is preferred for the frontend."
        )

        react = next(
            entity
            for entity in result.entities
            if entity.canonical_name == "React"
        )

        assert react.requirement_level == RequirementLevel.NICE_TO_HAVE

    def test_detects_forbidden_technology(self):
        result = extract_tech_stack(
            "Do not use MySQL in the proposed solution."
        )

        mysql = next(
            entity
            for entity in result.entities
            if entity.canonical_name == "MySQL"
        )

        assert mysql.requirement_level == RequirementLevel.FORBIDDEN

    def test_removes_duplicate_technologies(self):
        result = extract_tech_stack(
            "Python is required. The backend should be written in Python."
        )

        python_entities = [
            entity
            for entity in result.entities
            if entity.canonical_name == "Python"
        ]

        assert len(python_entities) == 1

    def test_empty_input_raises_error(self):
        with pytest.raises(EmptyInputError):
            extract_tech_stack("")

    def test_compatibility_with_company_stack(self):
        result = extract_tech_stack(
            "Python and PostgreSQL are required.",
            company_stack=["Python", "React"],
        )

        assert result.compatibility is not None
        assert "Python" in result.compatibility.matched
        assert "PostgreSQL" in result.compatibility.missing
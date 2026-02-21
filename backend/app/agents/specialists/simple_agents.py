"""
Simple specialist agents that delegate entirely to _default_generate.

These agents add no custom logic beyond configuring DOMAIN and SYSTEM_PROMPT.
Agents with domain-specific logic (financial, technical) live in their own files.
"""

from typing import List

from langchain_core.documents import Document

from app.agents.base import BaseSpecialistAgent
from app.agents.prompts import LEGAL_PROMPT, GENERAL_PROMPT, TIMELINE_PROMPT, REQUIREMENTS_PROMPT


class LegalSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for legal and regulatory aspects of RFPs."""

    DOMAIN: str = "legal"
    SYSTEM_PROMPT: str = LEGAL_PROMPT

    async def generate(self, question: str, context: List[Document]) -> str:
        return await self._default_generate(question, context)


class GeneralSpecialistAgent(BaseSpecialistAgent):
    """General-purpose specialist agent for comprehensive RFP analysis."""

    DOMAIN: str = "general"
    SYSTEM_PROMPT: str = GENERAL_PROMPT

    async def generate(self, question: str, context: List[Document]) -> str:
        return await self._default_generate(question, context)


class TimelineSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for schedules and timelines in RFPs."""

    DOMAIN: str = "timeline"
    SYSTEM_PROMPT: str = TIMELINE_PROMPT

    async def generate(self, question: str, context: List[Document]) -> str:
        return await self._default_generate(question, context)


class RequirementsSpecialistAgent(BaseSpecialistAgent):
    """Specialist agent for eligibility and requirements analysis."""

    DOMAIN: str = "requirements"
    SYSTEM_PROMPT: str = REQUIREMENTS_PROMPT

    async def generate(self, question: str, context: List[Document]) -> str:
        return await self._default_generate(question, context)

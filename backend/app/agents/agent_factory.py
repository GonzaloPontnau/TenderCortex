"""
Agent Factory — creates specialist agents by domain.

Uses the Factory pattern with a class-level registry. LLM and logger
are injected at instantiation time.
"""

from typing import Dict, Optional, Type

from app.agents.base import BaseSpecialistAgent, LLMProtocol, LoggerProtocol
from app.agents.prompts import DomainType, AVAILABLE_DOMAINS


class AgentFactory:
    """Factory for creating specialist agents by domain.

    Maintains a registry of domain → agent-class mappings and
    instantiates the appropriate class with injected dependencies.

    Example:
        >>> factory = AgentFactory(llm=my_llm, logger=my_logger)
        >>> financial_agent = factory.create("financial")
        >>> response = await financial_agent.generate(question, docs)
    """

    _registry: Dict[str, Type[BaseSpecialistAgent]] = {}
    _initialized: bool = False

    def __init__(
        self,
        llm: LLMProtocol,
        logger: Optional[LoggerProtocol] = None,
    ) -> None:
        self._llm = llm
        self._logger = logger

        if not AgentFactory._initialized:
            self._initialize_registry()

    @classmethod
    def _initialize_registry(cls) -> None:
        """Lazily import and register all agent classes to avoid circular imports."""
        from app.agents.specialists import (
            FinancialSpecialistAgent,
            LegalSpecialistAgent,
            TechnicalSpecialistAgent,
            TimelineSpecialistAgent,
            RequirementsSpecialistAgent,
            GeneralSpecialistAgent,
        )

        cls._registry = {
            "financial": FinancialSpecialistAgent,
            "legal": LegalSpecialistAgent,
            "technical": TechnicalSpecialistAgent,
            "timeline": TimelineSpecialistAgent,
            "requirements": RequirementsSpecialistAgent,
            "general": GeneralSpecialistAgent,
            # "quantitative" is handled by quant_node, not specialist_node
        }
        cls._initialized = True

    def create(self, domain: str) -> BaseSpecialistAgent:
        """Create a specialist agent for the given domain.

        Args:
            domain: Domain identifier (e.g. 'financial', 'legal').

        Returns:
            Instantiated specialist agent.

        Raises:
            ValueError: If domain is not in AVAILABLE_DOMAINS.
            NotImplementedError: If domain has no registered agent class.
        """
        if domain not in AVAILABLE_DOMAINS:
            raise ValueError(
                f"Unknown domain: '{domain}'. "
                f"Valid domains are: {AVAILABLE_DOMAINS}"
            )

        agent_class = self._registry.get(domain)
        if agent_class is None:
            raise NotImplementedError(
                f"Agent for domain '{domain}' has no registered class. "
                f"Registered domains: {list(self._registry.keys())}"
            )

        return agent_class(llm=self._llm, logger=self._logger)

    @classmethod
    def register(cls, domain: str, agent_class: Type[BaseSpecialistAgent]) -> None:
        """Register an agent class for a domain (useful for testing/plugins)."""
        if domain not in AVAILABLE_DOMAINS:
            raise ValueError(
                f"Cannot register unknown domain: '{domain}'. "
                f"Valid domains are: {AVAILABLE_DOMAINS}"
            )
        cls._registry[domain] = agent_class

    @classmethod
    def get_migrated_domains(cls) -> list:
        """Return the list of domains that have a registered agent class."""
        return list(cls._registry.keys())

    @classmethod
    def is_migrated(cls, domain: str) -> bool:
        """Return True if domain has a registered agent class."""
        return domain in cls._registry

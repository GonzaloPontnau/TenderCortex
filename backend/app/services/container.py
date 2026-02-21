"""Dependency injection container for shared application services."""

from functools import lru_cache
from typing import Optional

from app.core.logging import AgentLogger
from app.services.llm_factory import get_llm


class DependencyContainer:
    """Centralized container for lazy-initialized application dependencies."""

    def __init__(self) -> None:
        self._llm = None
        self._agent_factory = None
        self._logger: Optional[AgentLogger] = None

    @property
    def llm(self):
        """Cached LLM service instance."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    @property
    def logger(self) -> AgentLogger:
        """Cached AgentLogger instance."""
        if self._logger is None:
            self._logger = AgentLogger("container")
        return self._logger

    @property
    def agent_factory(self):
        """Cached AgentFactory initialized with container's LLM and logger."""
        if self._agent_factory is None:
            from app.agents.agent_factory import AgentFactory
            self._agent_factory = AgentFactory(
                llm=self.llm,
                logger=self.logger,
            )
        return self._agent_factory

    def reset(self) -> None:
        """Clear all cached services (useful for test isolation)."""
        self._llm = None
        self._agent_factory = None
        self._logger = None

    def override_llm(self, mock_llm) -> None:
        """Replace the LLM service and reset the factory to pick up the change."""
        self._llm = mock_llm
        self._agent_factory = None


@lru_cache(maxsize=1)
def get_container() -> DependencyContainer:
    """Return the global DependencyContainer singleton."""
    return DependencyContainer()


def reset_container() -> None:
    """Clear the lru_cache so a fresh container is created on next call."""
    get_container.cache_clear()

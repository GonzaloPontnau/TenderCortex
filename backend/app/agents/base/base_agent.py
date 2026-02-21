"""Abstract base class for all domain-specific specialist agents."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, runtime_checkable

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.agents.prompts import get_full_prompt, RESPONSE_FORMAT_TEMPLATE
from app.core.exceptions import AgentProcessingError


# =============================================================================
# PROTOCOLS (For Dependency Injection)
# =============================================================================


@runtime_checkable
class LLMProtocol(Protocol):
    """Interface for injectable LLM services (runtime_checkable for isinstance)."""

    async def ainvoke(self, messages: List[BaseMessage]) -> Any: ...


@runtime_checkable
class LoggerProtocol(Protocol):
    """Interface for injectable agent loggers."""

    def node_enter(self, node_name: str, state: dict) -> None: ...
    def node_exit(self, node_name: str, message: str) -> None: ...
    def debug(self, node_name: str, message: str) -> None: ...
    def error(self, node_name: str, error: Exception) -> None: ...


# =============================================================================
# BASE AGENT CLASS
# =============================================================================


class BaseSpecialistAgent(ABC):
    """Abstract base for domain-specific specialist agents.

    Subclasses must override DOMAIN, SYSTEM_PROMPT, and implement generate().
    """

    # Override these in subclasses
    DOMAIN: str = "general"
    SYSTEM_PROMPT: str = ""

    def __init__(
        self,
        llm: LLMProtocol,
        logger: Optional[LoggerProtocol] = None,
    ) -> None:
        self._llm = llm
        self._logger = logger

    @property
    def domain(self) -> str:
        """Return the domain this specialist handles."""
        return self.DOMAIN

    @property
    def node_name(self) -> str:
        """Return the node name for logging purposes."""
        return f"specialist_{self.DOMAIN}"

    # -------------------------------------------------------------------------
    # Abstract Methods (Must be implemented by subclasses)
    # -------------------------------------------------------------------------

    @abstractmethod
    async def generate(
        self,
        question: str,
        context: List[Document],
    ) -> str:
        """
        Generate a response for the given question using the context.

        This is the main method that subclasses must implement.
        It should use the specialist's domain-specific logic to
        produce an appropriate response.

        Args:
            question: The user's question.
            context: List of relevant documents for context.

        Returns:
            The generated response string.

        Raises:
            AgentProcessingError: If generation fails.
        """
        pass

    # -------------------------------------------------------------------------
    # Concrete Helper Methods
    # -------------------------------------------------------------------------

    def _format_context(
        self,
        context: List[Document],
        separator: str = "\n\n---\n\n",
        max_length: Optional[int] = None,
    ) -> str:
        """Join document contents into a single string for prompt inclusion."""
        if not context:
            return ""

        formatted = separator.join(doc.page_content for doc in context)

        if max_length and len(formatted) > max_length:
            formatted = formatted[:max_length] + "\n\n[Contexto truncado...]"

        return formatted

    def _build_messages(
        self,
        question: str,
        context_text: str,
        system_prompt: Optional[str] = None,
        include_response_format: bool = True,
    ) -> List[BaseMessage]:
        """Build [SystemMessage, HumanMessage] list for LLM invocation."""
        # Use provided prompt or get from prompts module
        if system_prompt:
            full_system = system_prompt
            if include_response_format:
                full_system = f"{system_prompt}\n\n{RESPONSE_FORMAT_TEMPLATE}"
        else:
            full_system = get_full_prompt(self.DOMAIN, include_response_format)

        user_content = (
            f"Contexto del documento:\n{context_text}\n\n"
            f"Pregunta: {question}"
        )

        return [
            SystemMessage(content=full_system),
            HumanMessage(content=user_content),
        ]

    def _log_enter(self, state: Optional[dict] = None) -> None:
        """Log entry into the specialist node."""
        if self._logger:
            self._logger.node_enter(self.node_name, state or {})

    def _log_exit(self, message: str) -> None:
        """Log exit from the specialist node."""
        if self._logger:
            self._logger.node_exit(self.node_name, message)

    def _log_debug(self, message: str) -> None:
        """Log debug message."""
        if self._logger:
            self._logger.debug(self.node_name, message)

    def _log_error(self, error: Exception) -> None:
        """Log error."""
        if self._logger:
            self._logger.error(self.node_name, error)

    # -------------------------------------------------------------------------
    # Default Generate Implementation (Optional override)
    # -------------------------------------------------------------------------

    async def _default_generate(
        self,
        question: str,
        context: List[Document],
    ) -> str:
        """
        Default implementation of generate logic.

        Subclasses can call this method or override completely.
        This provides a standard flow: format context, build messages, invoke LLM.

        Args:
            question: The user's question.
            context: List of relevant documents for context.

        Returns:
            The generated response string.

        Raises:
            AgentProcessingError: If the LLM invocation fails.
        """
        self._log_enter({"question": question, "context_size": len(context)})

        try:
            context_text = self._format_context(context)

            if not context_text.strip():
                self._log_exit("No context available")
                return "No encontré información relevante para responder tu pregunta."

            self._log_debug(f"Using {len(context)} docs for generation")

            messages = self._build_messages(question, context_text)
            response = await self._llm.ainvoke(messages)
            answer = response.content

            self._log_exit(f"{len(answer)} chars generated")
            return answer

        except Exception as e:
            self._log_error(e)
            raise AgentProcessingError(
                message=f"Failed to generate {self.DOMAIN} response",
                agent_name=self.node_name,
                original_error=e,
            )

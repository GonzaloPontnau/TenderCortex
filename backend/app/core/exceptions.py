"""Custom exceptions for TenderCortex."""

from typing import Optional


class CortexBaseException(Exception):
    """Base exception for all TenderCortex errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AgentProcessingError(CortexBaseException):
    """Raised when an agent fails to process a request.

    Attributes:
        agent_name: Name/identifier of the agent that failed.
        original_error: The underlying exception if available.
    """

    def __init__(
        self,
        message: str,
        agent_name: str,
        original_error: Optional[Exception] = None,
        details: Optional[str] = None,
    ) -> None:
        self.agent_name = agent_name
        self.original_error = original_error

        enhanced_message = f"[Agent: {agent_name}] {message}"
        if original_error:
            enhanced_message = (
                f"{enhanced_message} | Caused by: "
                f"{type(original_error).__name__}: {str(original_error)[:200]}"
            )

        super().__init__(enhanced_message, details)

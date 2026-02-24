---
module: backend/app/services/container.py
type: service
version: "1.0.0"
status: approved
---

# SPEC: DependencyContainer

## Purpose

Centralized dependency injection container providing lazy-initialized, cached instances of LLM, AgentFactory, and AgentLogger. Supports test isolation via `override_llm()` and `reset()`.

## Public Interface

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `llm` | `@property` | `ChatGroq` | Lazy-loaded LLM singleton |
| `logger` | `@property` | `AgentLogger` | Lazy-loaded logger |
| `agent_factory` | `@property` | `AgentFactory` | Factory initialized with container's LLM/logger |
| `reset` | `def reset() -> None` | `None` | Clear all cached services |
| `override_llm` | `def override_llm(mock) -> None` | `None` | Replace LLM for testing, resets factory |
| `get_container` | `def get_container() -> DependencyContainer` | Singleton | Module-level singleton via `lru_cache` |
| `reset_container` | `def reset_container() -> None` | `None` | Clear singleton cache |

## Dependencies

### Internal
| Module | Purpose |
|--------|---------|
| `app.services.llm_factory` | LLM instance creation |
| `app.agents.agent_factory` | Agent creation (lazy import) |
| `app.core.logging` | AgentLogger |

## Configuration

None — delegates to `llm_factory` and `AgentFactory` for configuration.

## Error Handling

| Error Condition | Behavior | Recovery |
|-----------------|----------|----------|
| LLM initialization failure | Propagates from `get_llm()` | Caller handles |
| Import error (AgentFactory) | Raised on first `agent_factory` access | Fix import |

## Invariants

- `override_llm()` always resets `_agent_factory` to ensure factory uses new LLM
- `reset()` clears all three cached services
- `get_container()` returns same instance on repeated calls (lru_cache maxsize=1)
- `reset_container()` forces new instance on next call

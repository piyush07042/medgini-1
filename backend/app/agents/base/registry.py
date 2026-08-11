"""
Agent Registry for MediGenie.

Provides a central registry for all AI agents.
The Supervisor uses this registry to discover and execute agents.

Benefits
--------
- Loose coupling
- Easy extensibility
- Dependency Injection friendly
- No hardcoded agent imports
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable

from .base_agent import BaseAgent


logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for all MediGenie agents.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent instance.
        """
        name = agent.agent_name

        if name in self._agents:
            raise ValueError(
                f"Agent '{name}' is already registered."
            )

        self._agents[name] = agent

        logger.info("Registered agent: %s", name)

    def unregister(self, agent_name: str) -> None:
        """
        Remove an agent.
        """

        self._agents.pop(agent_name, None)

        logger.info("Unregistered agent: %s", agent_name)

    def get(self, agent_name: str) -> BaseAgent:
        """
        Retrieve a registered agent.
        """

        if agent_name not in self._agents:
            raise KeyError(
                f"Agent '{agent_name}' not found."
            )

        return self._agents[agent_name]

    def exists(self, agent_name: str) -> bool:
        """
        Check if an agent exists.
        """
        return agent_name in self._agents

    def all(self) -> Iterable[BaseAgent]:
        """
        Return all registered agents.
        """
        return self._agents.values()

    def names(self) -> list[str]:
        """
        List registered agent names.
        """
        return sorted(self._agents.keys())

    def clear(self) -> None:
        """
        Remove every registered agent.
        """
        self._agents.clear()

        logger.info("Agent registry cleared.")

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, item: str) -> bool:
        return item in self._agents

    def __repr__(self) -> str:
        return (
            f"AgentRegistry("
            f"{len(self._agents)} agents)"
        )
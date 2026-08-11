"""
Shared application resources.
"""

from __future__ import annotations

from typing import Any


class ResourceManager:
    """
    Stores reusable application resources.
    """

    def __init__(self) -> None:
        self._resources: dict[str, Any] = {}

    def register(
        self,
        name: str,
        resource: Any,
    ) -> None:
        self._resources[name] = resource

    def get(
        self,
        name: str,
    ) -> Any:
        return self._resources.get(name)

    def remove(
        self,
        name: str,
    ) -> None:
        self._resources.pop(name, None)

    def clear(self) -> None:
        self._resources.clear()


resource_manager = ResourceManager()
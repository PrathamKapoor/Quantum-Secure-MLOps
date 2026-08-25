'''Agent registry to discover and retrieve agent implementations.'''
\nfrom __future__ import annotations\n\nfrom typing import Dict, Type\n\nfrom .base import BaseAgent\n\n\nclass AgentRegistry:\n    def __init__(self) -> None:\n        self._registry: Dict[str, Type[BaseAgent]] = {}
\n    def register(self, name: str, agent_cls: Type[BaseAgent]) -> None:\n        self._registry[name] = agent_cls
\n    def get(self, name: str) -> Type[BaseAgent]:\n        return self._registry[name]\n
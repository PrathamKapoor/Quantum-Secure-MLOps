'''Orchestrator tying the MLOps stages together.'''

from __future__ import annotations

from typing import Any, Dict


class LifecycleOrchestrator:
    def __init__(self, pipeline: Any, trainer: Any, evaluator: Any, packager: Any, deployer: Any) -> None:
        self.pipeline = pipeline
        self.trainer = trainer
        self.evaluator = evaluator
        self.packager = packager
        self.deployer = deployer

    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the full end‑to‑end lifecycle and return a summary dict.

        Each sub‑component is expected to follow the contracts defined in the
        sibling modules.
        """
        raise NotImplementedError

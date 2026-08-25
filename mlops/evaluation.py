'''Evaluation service contracts.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class EvaluationReport:
    model_name: str
    dataset_id: str
    metrics: Dict[str, float]
    passed: bool

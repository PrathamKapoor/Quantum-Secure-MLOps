'''Training service contracts.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TrainingRequest:
    model_name: str
    dataset_id: str
    hyperparameters: Dict[str, Any]


@dataclass
class TrainingJob:
    job_id: str
    request: TrainingRequest


@dataclass
class TrainingResult:
    job_id: str
    artifact_digest: str
    metrics: Dict[str, float]

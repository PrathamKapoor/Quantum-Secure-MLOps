'''Deployment service contract.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class DeploymentRequest:
    model_name: str
    version_id: str
    target_environment: str  # e.g., 'staging', 'production'


@dataclass
class DeploymentResult:
    deployment_id: str
    status: str  # e.g., 'deployed', 'failed'
    details: Dict[str, Any]

'''Packaging service contract.'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PackageInfo:
    model_name: str
    version: int
    artifact_digest: str
    metadata: Dict[str, Any]

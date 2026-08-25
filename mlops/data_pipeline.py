'''Data pipeline contract for the MLOps layer.'''

from __future__ import annotations

from typing import Any, Dict


class DataPipeline:
    def run(self, config: Dict[str, Any]) -> Any:
        """Execute the data preparation steps and return the dataset object."""
        raise NotImplementedError

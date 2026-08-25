'''Workflow Engine contracts for external callers.'''
\nfrom __future__ import annotations
\nfrom typing import Any, Dict
\n\nclass WorkflowInterface:\n    """Expose workflow actions to external clients (UI, API, CLI)."""
\n    def start_workflow(self, definition: Dict[str, Any]) -> str:
        """Instantiate a new workflow and return its identifier."""
        raise NotImplementedError
\n    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Retrieve the current state and progress of a workflow."""
        raise NotImplementedError\n
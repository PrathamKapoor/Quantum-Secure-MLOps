'''User Interaction Layer contracts.

Defines the backend contract for user-facing operations such as request
submission, status retrieval, approval actions and visibility queries.
'''\n\nfrom __future__ import annotations\n\nfrom typing import Any, Dict\n\n\nclass UserInterface:\n    """Contract for UI‑driven interactions.
\n    Implementations may expose HTTP endpoints, CLI commands or RPC calls.
    The methods return plain data structures that can be serialized.
    """\n\n    def submit_request(self, request: Dict[str, Any]) -> str:\n        """Accept a new request and return a unique request identifier."""\n        raise NotImplementedError\n\n    def get_status(self, request_id: str) -> Dict[str, Any]:\n        """Return the current status of a request (e.g., CREATED, RUNNING, DONE)."""\n        raise NotImplementedError\n\n    def approve_action(self, request_id: str, approval: bool) -> None:\n        """Record an approval or rejection for a pending action."""\n        raise NotImplementedError\n\n    def get_visibility(self, user_id: str) -> Dict[str, Any]:\n        """Provide system‑wide visibility information for a given user."""\n        raise NotImplementedError\n
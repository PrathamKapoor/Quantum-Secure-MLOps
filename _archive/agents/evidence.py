'''Evidence generation helpers for agents.'''
\nfrom __future__ import annotations\n\nfrom typing import Any, Dict\n\n\ndef generate_evidence(agent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:\n    """Create a simple evidence packet from agent output."""
    return {"agent": agent_name, "evidence": data}\n
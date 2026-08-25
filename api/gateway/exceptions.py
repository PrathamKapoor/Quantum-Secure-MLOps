'''Custom API exception types.'''
\nfrom __future__ import annotations\n\nfrom fastapi import HTTPException\n\n\nclass APIError(HTTPException):\n    """Base class for API‑level errors with a default status code of 400."""
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(status_code=status_code, detail=detail)\n
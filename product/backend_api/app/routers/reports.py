from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..services.report_service import get_reports, PROJECT_ROOT

router = APIRouter()

# Only these project-relative directories may be served.
ALLOWED_ROOTS = ("reports", "artifacts", "docs")


@router.get("")
async def get_reports_list():
    return get_reports()


@router.get("/file")
async def get_report_file(path: str = Query(..., description="Project-relative report path")):
    """Serve a report file from whitelisted project directories.

    Read-only and restricted to reports/, artifacts/ and docs/ to keep the
    research system immutable from the product layer.
    """
    candidate = (PROJECT_ROOT / path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    root = candidate.relative_to(PROJECT_ROOT).parts[:1]
    if not root or root[0] not in ALLOWED_ROOTS:
        raise HTTPException(status_code=403, detail="Path not in allowed report roots")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(candidate, filename=Path(path).name)

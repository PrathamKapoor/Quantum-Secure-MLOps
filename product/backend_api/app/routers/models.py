from fastapi import APIRouter, HTTPException

from ..services import model_service

router = APIRouter()


@router.get("")
async def get_models_list():
    return model_service.get_models()


@router.get("/{model_name}/versions")
async def get_model_versions(model_name: str):
    versions = model_service.get_versions(model_name)
    if not versions:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found.")
    return {"model_name": model_name, "versions": versions}


@router.get("/{model_name}/versions/{version_id}")
async def get_model_version_detail(model_name: str, version_id: str):
    detail = model_service.get_version_detail(model_name, version_id)
    if detail is None:
        raise HTTPException(
            status_code=404,
            detail=f"Version '{version_id}' not found for model '{model_name}'.",
        )
    return detail

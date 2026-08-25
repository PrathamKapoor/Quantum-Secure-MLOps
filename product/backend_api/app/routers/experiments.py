from fastapi import APIRouter, HTTPException

from ..schemas.experiment import ExperimentDetail, ExperimentList
from ..services import experiment_service

router = APIRouter()


@router.get("", response_model=ExperimentList)
async def get_experiments():
    return experiment_service.list_experiments()


@router.get("/{experiment_id}", response_model=ExperimentDetail)
async def get_experiment_detail(experiment_id: int):
    detail = experiment_service.get_experiment(experiment_id)
    if detail is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment '{experiment_id}' not found."
        )
    return detail

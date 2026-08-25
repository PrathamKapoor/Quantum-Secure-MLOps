from pydantic import BaseModel, Field


class ExperimentSummary(BaseModel):
    experiment_id: str
    name: str
    lifecycle_stage: str | None = None
    run_count: int = 0


class ExperimentList(BaseModel):
    available: bool
    experiments: list[ExperimentSummary]
    note: str = ""


class ExperimentRun(BaseModel):
    run_id: str
    name: str | None = None
    status: str | None = None
    start_time: int | None = None
    end_time: int | None = None
    params: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)


class ExperimentDetail(BaseModel):
    available: bool
    experiment: ExperimentSummary
    runs: list[ExperimentRun]

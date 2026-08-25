from pydantic import BaseModel


class ModelVersion(BaseModel):
    """Registry version record; fields mirror the research registry row."""

    model_name: str
    version: int
    version_id: str
    state: str | None = None
    created_at: float | str | None = None

    class Config:
        extra = "allow"


class ModelVersionDetail(ModelVersion):
    passport_id: str | None = None
    feature_set: str | None = None
    signature_suite: str | None = None
    signed_by: str | None = None


class ModelVersionsResponse(BaseModel):
    model_name: str
    versions: list[dict]

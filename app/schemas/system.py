from pydantic import BaseModel


class RootResponse(BaseModel):
    name: str
    version: str


class HealthResponse(BaseModel):
    status: str
    service: str


class DependencyCheck(BaseModel):
    name: str
    available: bool
    detail: str


class ReadinessResponse(BaseModel):
    status: str
    service: str
    checks: list[DependencyCheck]

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "GuardedRAG API"
    app_version: str = "0.1.0"
    service_name: str = "guardedrag"


settings = Settings()


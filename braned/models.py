from pydantic import BaseModel


class TargetDirectory(BaseModel):
    path: str
    vector_store: str


class ConfigModel(BaseModel):
    target_directories: list[TargetDirectory]

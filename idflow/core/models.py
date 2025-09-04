from pydantic import BaseModel, Field
from typing import Any, Dict

class DocRef(BaseModel):
    key: str
    uuid: str
    data: Dict[str, Any] = Field(default_factory=dict)

class FileRef(BaseModel):
    key: str
    filename: str
    uuid: str
    data: Dict[str, Any] = Field(default_factory=dict)

VALID_STATUS = {"inbox","active","done","blocked","archived"}

# Stage-specific statuses (different from Document statuses)
VALID_STAGE_STATUS = {"scheduled", "active", "done", "blocked", "cancelled"}


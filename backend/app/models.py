from pydantic import BaseModel, Field
from typing import Literal

class Incident(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    service: str = Field(min_length=2, max_length=100)
    severity: Literal["SEV1", "SEV2", "SEV3"] = "SEV2"
    logs: list[str] = Field(min_length=1, max_length=100)
    recent_changes: list[str] = Field(default_factory=list)

class Finding(BaseModel):
    root_cause: str
    evidence: list[str]
    remediation: str
    confidence: float = Field(ge=0, le=1)
    risk: Literal["low", "medium", "high"]

class Approval(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=2)

class Run(BaseModel):
    id: str
    status: Literal["awaiting_approval", "approved", "rejected", "executed", "failed"]
    incident: Incident
    finding: Finding
    action: dict | None = None
    trace: list[dict] = Field(default_factory=list)

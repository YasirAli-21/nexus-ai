from pydantic import BaseModel
from typing import List, Dict, Any


class IncidentSummary(BaseModel):

    incident_id: str
    service: str
    severity: str
    status: str
    anomaly_count: int


class IncidentResponse(BaseModel):

    incident: Dict[str, Any]
    evidence: Dict[str, Any]
    investigation: Dict[str, Any]
    timeline: List[Dict[str, Any]]
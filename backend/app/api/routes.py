from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent
from backend.app.models.workflow import RemediationWorkflow, WorkflowAuditEvent


router = APIRouter(
    prefix="/api",
    tags=["NEXUS AI"],
)


# ==========================================
# API STATUS
# ==========================================

@router.get("/")
def api_status():

    return {
        "system": "NEXUS AI",
        "status": "operational",
        "version": "0.1.0",
    }


# ==========================================
# LIST ALL INCIDENTS
# ==========================================

@router.get("/incidents")
def get_incidents(
    db: Session = Depends(get_db),
):

    incidents = (
        db.query(Incident)
        .order_by(Incident.detected_at.desc())
        .all()
    )

    return {
        "system": "NEXUS AI",
        "count": len(incidents),
        "incidents": [
            {
                "id": incident.id,
                "service": incident.service,
                "severity": incident.severity,
                "status": incident.status,
                "detected_at": incident.detected_at,
                "root_cause": incident.root_cause,
                "confidence": incident.confidence,
            }
            for incident in incidents
        ],
    }


# ==========================================
# GET INCIDENT DETAILS
# ==========================================

@router.get("/incidents/{incident_id}")
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
):

    # ------------------------------------------
    # Find incident
    # ------------------------------------------

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:

        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found.",
        )

    # ------------------------------------------
    # Get evidence
    # ------------------------------------------

    evidence = (
        db.query(Evidence)
        .filter(Evidence.incident_id == incident_id)
        .all()
    )

    # ------------------------------------------
    # Get timeline
    # ------------------------------------------

    timeline = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.incident_id == incident_id)
        .order_by(TimelineEvent.timestamp.asc())
        .all()
    )

    # ------------------------------------------
    # Categorize evidence
    # ------------------------------------------

    metrics_evidence = []
    log_evidence = []
    database_evidence = []
    other_evidence = []

    for item in evidence:

        evidence_item = {
            "id": item.id,
            "type": item.evidence_type,
            "details": item.details,
        }

        evidence_type = item.evidence_type.lower()

        if "metric" in evidence_type or evidence_type in {
            "max_cpu",
            "max_memory",
            "max_latency",
            "max_error_rate",
        }:

            metrics_evidence.append(evidence_item)

        elif "log" in evidence_type:

            log_evidence.append(evidence_item)

        elif "database" in evidence_type:

            database_evidence.append(evidence_item)

        else:

            other_evidence.append(evidence_item)

    # ------------------------------------------
    # Categorize timeline
    # ------------------------------------------

    metric_timeline = []
    log_timeline = []
    other_timeline = []

    for event in timeline:

        timeline_item = {
            "id": event.id,
            "timestamp": event.timestamp,
            "type": event.event_type,
            "description": event.description,
        }

        event_type = event.event_type.upper()

        if event_type == "METRIC":

            metric_timeline.append(timeline_item)

        elif event_type == "LOG":

            log_timeline.append(timeline_item)

        else:

            other_timeline.append(timeline_item)

    # ------------------------------------------
    # Final response
    # ------------------------------------------

    return {

        "system": "NEXUS AI",

        "incident": {
            "id": incident.id,
            "service": incident.service,
            "severity": incident.severity,
            "status": incident.status,
            "detected_at": incident.detected_at,
        },

        "investigation": {
            "root_cause": incident.root_cause,
            "confidence": incident.confidence,
        },

        "evidence": {

            "summary": {
                "total": len(evidence),
                "metrics": len(metrics_evidence),
                "logs": len(log_evidence),
                "database": len(database_evidence),
                "other": len(other_evidence),
            },

            "metrics": metrics_evidence,

            "logs": log_evidence,

            "database": database_evidence,

            "other": other_evidence,
        },

        "timeline": {

            "summary": {
                "total": len(timeline),
                "metrics": len(metric_timeline),
                "logs": len(log_timeline),
                "other": len(other_timeline),
            },

            "metrics": metric_timeline,

            "logs": log_timeline,

            "other": other_timeline,
        },
    }

# ==========================================
# HUMAN APPROVAL & SAFE SIMULATION WORKFLOW
# ==========================================

class ApprovalDecision(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    reviewer: str = Field(min_length=2, max_length=100)


def _workflow_response(workflow):
    return {
        "incident_id": workflow.incident_id,
        "approval_status": workflow.approval_status,
        "remediation_status": workflow.remediation_status,
        "reviewer": workflow.reviewer,
        "decision_at": workflow.decision_at,
        "simulation_result": workflow.simulation_result,
    }


@router.get("/incidents/{incident_id}/workflow")
def get_workflow(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    workflow = db.get(RemediationWorkflow, incident_id)

    audit = db.query(WorkflowAuditEvent).filter(
        WorkflowAuditEvent.incident_id == incident_id
    ).order_by(WorkflowAuditEvent.timestamp.asc(),
               WorkflowAuditEvent.id.asc()).all()

    state = _workflow_response(workflow) if workflow else {
        "incident_id": incident_id,
        "approval_status": "PENDING",
        "remediation_status": "NOT_STARTED",
        "reviewer": None,
        "decision_at": None,
        "simulation_result": None,
    }

    state["audit"] = [
        {
            "id": event.id,
            "action": event.action,
            "actor": event.actor,
            "details": event.details,
            "timestamp": event.timestamp,
        }
        for event in audit
    ]
    return state


@router.post("/incidents/{incident_id}/approval")
def decide_approval(
    incident_id: str,
    payload: ApprovalDecision,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    workflow = db.get(RemediationWorkflow, incident_id)

    if workflow is None:
        workflow = RemediationWorkflow(
            incident_id=incident_id,
            approval_status="PENDING",
            remediation_status="NOT_STARTED",
        )
        db.add(workflow)
        db.flush()

    if workflow.approval_status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Decision already recorded: {workflow.approval_status}",
        )

    now = datetime.utcnow()
    workflow.approval_status = (
        "APPROVED" if payload.decision == "APPROVE" else "REJECTED"
    )
    workflow.reviewer = payload.reviewer.strip()
    workflow.decision_at = now

    db.add(WorkflowAuditEvent(
        incident_id=incident_id,
        action=workflow.approval_status,
        actor=workflow.reviewer,
        details=f"Human approval decision recorded for {incident_id}.",
        timestamp=now,
    ))

    try:
        db.commit()
        db.refresh(workflow)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Could not save approval decision"
        )

    return _workflow_response(workflow)


@router.post("/incidents/{incident_id}/remediation/simulate")
def simulate_remediation(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    workflow = db.get(RemediationWorkflow, incident_id)

    if workflow is None or workflow.approval_status != "APPROVED":
        raise HTTPException(
            status_code=403,
            detail="Human approval is required before remediation.",
        )

    if workflow.remediation_status == "SIMULATED":
        raise HTTPException(
            status_code=409,
            detail="Simulation has already been recorded for this incident.",
        )

    now = datetime.utcnow()
    result = (
        f"SIMULATION ONLY: A proposed recovery action for "
        f"{incident.service} was simulated. No production systems, "
        f"services, databases, or infrastructure were changed."
    )

    workflow.remediation_status = "SIMULATED"
    workflow.simulation_result = result

    db.add(WorkflowAuditEvent(
        incident_id=incident_id,
        action="REMEDIATION_SIMULATED",
        actor=workflow.reviewer or "recorded-reviewer",
        details=result,
        timestamp=now,
    ))

    try:
        db.commit()
        db.refresh(workflow)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Could not save simulation result"
        )

    return _workflow_response(workflow)


"""
NEXUS AI - Phase 8
On-demand AI incident investigation.

Default: deterministic investigation (free, no API key).
Optional: LLM investigation (requires OPENAI_API_KEY).

No infrastructure remediation is executed.
Existing approval and audit records are untouched.
"""

import json
import os
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.investigator.investigator import AIInvestigator
from backend.app.core.database import get_db
from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence


router = APIRouter(
    prefix="/api/incidents",
    tags=["AI Investigation"],
)

REPORT_TYPE = "AI_INVESTIGATION_REPORT"


class InvestigationRequest(BaseModel):
    mode: Literal["DETERMINISTIC", "LLM"] = "DETERMINISTIC"


def parse_json(value):
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value


def to_number(value):
    try:
        number = float(value)
        return number if number >= 0 else 0.0
    except (ValueError, TypeError):
        return 0.0


def extract_evidence(db, incident):
    """
    Convert stored batch or live telemetry evidence
    into the format expected by AIInvestigator.
    """

    records = (
        db.query(Evidence)
        .filter(Evidence.incident_id == incident.id)
        .order_by(Evidence.id.asc())
        .all()
    )

    result = {
        "service": incident.service,
        "max_cpu": 0.0,
        "max_memory": 0.0,
        "max_latency": 0.0,
        "max_error_rate": 0.0,
        "error_logs": 0,
        "database_logs": 0,
        "database_messages": {},
    }

    metric_mapping = {
        "MAX_CPU": "max_cpu",
        "MAX_MEMORY": "max_memory",
        "MAX_LATENCY": "max_latency",
        "MAX_ERROR_RATE": "max_error_rate",
        "METRIC_CPU_USAGE": "max_cpu",
        "METRIC_MEMORY_USAGE": "max_memory",
        "METRIC_LATENCY_MS": "max_latency",
        "METRIC_ERROR_RATE": "max_error_rate",
    }

    found_metrics = set()

    for record in records:
        evidence_type = record.evidence_type.upper()
        value = parse_json(record.details)

        if evidence_type in metric_mapping:
            field = metric_mapping[evidence_type]

            if isinstance(value, dict):
                value = value.get("value", 0)

            numeric_value = to_number(value)

            result[field] = max(
                result[field],
                numeric_value,
            )
            found_metrics.add(field)

        elif evidence_type == "ERROR_LOGS":
            result["error_logs"] = int(to_number(value))

        elif evidence_type == "DATABASE_LOGS":
            result["database_logs"] = int(to_number(value))

        elif evidence_type == "DATABASE_MESSAGES":
            if isinstance(value, dict):
                result["database_messages"] = value

            elif isinstance(value, list):
                result["database_messages"] = {
                    str(message): 1 for message in value
                }

    return result, sorted(found_metrics)


def prepare_report(investigation, mode, evidence, metrics_found):
    recommendations = investigation.get("recommendations") or []
    findings = investigation.get("findings") or []

    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    if not isinstance(findings, list):
        findings = [str(findings)]

    # All suggested actions require human review.
    if not recommendations:
        recommendations = [
            "Review recent telemetry and application logs.",
            "Compare current metrics with the normal service baseline.",
            "Check recent deployments and configuration changes.",
        ]

    return {
        "investigation_mode": investigation.get(
            "investigation_mode", mode
        ),
        "root_cause": investigation.get(
            "root_cause",
            "Root cause could not be established.",
        ),
        "confidence": investigation.get("confidence", "LOW"),
        "findings": findings,
        "recommendations": recommendations,
        "metrics_analyzed": metrics_found,
        "evidence_summary": evidence,
        "generated_at": datetime.utcnow().isoformat(),
        "note": (
            "AI analysis is advisory. Root cause is not confirmed. "
            "No remediation was executed."
        ),
    }


def run_investigator(evidence, requested_mode):
    if requested_mode == "DETERMINISTIC":
        return AIInvestigator().investigate(evidence)

    # Load environment configuration only when LLM is explicitly requested.
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY is not configured. "
                "Use DETERMINISTIC mode instead."
            ),
        )

    try:
        from ai.investigator.llm_investigator import LLMInvestigator

        # Existing LLMInvestigator already includes
        # the deterministic fallback on LLM errors.
        return LLMInvestigator().investigate(evidence)

    except HTTPException:
        raise

    except Exception:
        # Do not expose secret configuration in error messages.
        fallback = AIInvestigator().investigate(evidence)
        fallback["investigation_mode"] = "DETERMINISTIC_FALLBACK"
        return fallback


@router.post("/{incident_id}/investigate")
def investigate_incident(
    incident_id: str,
    payload: InvestigationRequest,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    evidence, metrics_found = extract_evidence(db, incident)

    if not metrics_found:
        raise HTTPException(
            status_code=409,
            detail=(
                "No usable metric evidence is available "
                "for this incident."
            ),
        )

    investigation = run_investigator(
        evidence,
        payload.mode,
    )

    report = prepare_report(
        investigation,
        payload.mode,
        evidence,
        metrics_found,
    )

    # Save results without deleting any existing evidence.
    # Each investigation is retained as a separate record.
    try:
        db.add(
            Evidence(
                incident_id=incident_id,
                evidence_type=REPORT_TYPE,
                details=json.dumps(report, default=str),
            )
        )

        incident.root_cause = report["root_cause"]
        incident.confidence = report["confidence"]

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save investigation report.",
        )

    return {
        "status": "INVESTIGATION_COMPLETED",
        "incident_id": incident_id,
        "report": report,
    }


@router.get("/{incident_id}/investigation-report")
def get_investigation_report(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    record = (
        db.query(Evidence)
        .filter(
            Evidence.incident_id == incident_id,
            Evidence.evidence_type == REPORT_TYPE,
        )
        .order_by(Evidence.id.desc())
        .first()
    )

    if record is None:
        return {
            "incident_id": incident_id,
            "status": "NOT_INVESTIGATED",
            "report": None,
        }

    return {
        "incident_id": incident_id,
        "status": "AVAILABLE",
        "report": parse_json(record.details),
    }

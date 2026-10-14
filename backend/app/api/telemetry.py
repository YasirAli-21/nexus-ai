
"""
NEXUS AI - Phase 7
Persistent telemetry and serialized SQLite incident creation.

Development-only API. Do not expose publicly without
authentication, rate limits and access controls.
"""

import json
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent
from backend.app.models.telemetry import TelemetrySample
from backend.incident.engine import IncidentEngine
from ml.anomaly_detection.detector import AnomalyDetector, FEATURES


router = APIRouter(
    prefix="/api/telemetry",
    tags=["Telemetry Detection"],
)

ROOT = Path(__file__).resolve().parents[3]
NORMAL_CSV = ROOT / "data" / "synthetic" / "normal_metrics.csv"

COOLDOWN_MINUTES = 5
OBSERVATION_WINDOW_SECONDS = 120
ML_OBSERVATIONS_REQUIRED = 3


class TelemetryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str = Field(min_length=2, max_length=100)
    cpu_usage: float = Field(ge=0, le=100, allow_inf_nan=False)
    memory_usage: float = Field(ge=0, le=100, allow_inf_nan=False)
    latency_ms: float = Field(ge=0, le=1000000, allow_inf_nan=False)
    request_count: int = Field(ge=0)
    error_rate: float = Field(ge=0, le=100, allow_inf_nan=False)


@lru_cache(maxsize=1)
def get_detector():
    if not NORMAL_CSV.is_file():
        raise FileNotFoundError(
            f"Training dataset missing: {NORMAL_CSV}"
        )

    data = pd.read_csv(NORMAL_CSV)

    model = AnomalyDetector()
    model.train(data)

    return model


def detect(payload):
    frame = pd.DataFrame([payload.model_dump()])

    model = get_detector()

    result = model.predict(frame)

    ml_anomaly = bool(result.iloc[0]["is_anomaly"])

    score = float(
        model.model.decision_function(frame[FEATURES])[0]
    )

    critical = (
        payload.cpu_usage >= 90
        or payload.memory_usage >= 95
        or payload.latency_ms >= 2000
        or payload.error_rate >= 30
    )

    return {
        "model_anomaly": ml_anomaly,
        "threshold_anomaly": critical,
        "is_anomaly": ml_anomaly or critical,
        "decision_score": round(score, 5),
    }


def recent_incident(db, service, now):
    cutoff = now - timedelta(minutes=COOLDOWN_MINUTES)

    return (
        db.query(Incident)
        .filter(
            Incident.service == service,
            Incident.id.like("INC-LIVE-%"),
            Incident.detected_at >= cutoff,
        )
        .order_by(Incident.detected_at.desc())
        .first()
    )


def consecutive_anomaly_count(db, service, now):
    """
    Count consecutive ML-only anomalies in the last 120 seconds.

    A normal sample resets the sequence logically.
    All historical observations remain in the database.
    """

    cutoff = now - timedelta(
        seconds=OBSERVATION_WINDOW_SECONDS
    )

    recent = (
        db.query(TelemetrySample)
        .filter(
            TelemetrySample.service == service,
            TelemetrySample.observed_at >= cutoff,
            TelemetrySample.observed_at <= now,
        )
        .order_by(
            TelemetrySample.observed_at.desc(),
            TelemetrySample.id.desc(),
        )
        .limit(ML_OBSERVATIONS_REQUIRED)
        .all()
    )

    count = 0

    for sample in recent:
        if not sample.model_anomaly or sample.threshold_anomaly:
            break
        count += 1

    return count


def make_incident(db, payload, detection, count, now):
    incident_id = (
        f"INC-LIVE-{uuid.uuid4().hex[:12].upper()}"
    )

    frame = pd.DataFrame([payload.model_dump()])

    severity = IncidentEngine().calculate_severity(frame)

    if detection["threshold_anomaly"]:
        reason = "Critical operational threshold exceeded"
    else:
        reason = (
            f"{count} consecutive Isolation Forest anomalies "
            f"within {OBSERVATION_WINDOW_SECONDS} seconds"
        )

    summary = (
        f"Automated detection for {payload.service}. "
        f"Trigger: {reason}. "
        f"CPU {payload.cpu_usage}%, "
        f"memory {payload.memory_usage}%, "
        f"latency {payload.latency_ms} ms, "
        f"error rate {payload.error_rate}%. "
        "Root cause not confirmed; investigation required."
    )

    incident = Incident(
        id=incident_id,
        service=payload.service,
        severity=severity,
        status="NEW",
        detected_at=now,
        root_cause=summary,
        confidence=None,
    )

    db.add(incident)
    db.flush()

    metrics = {
        "cpu_usage": payload.cpu_usage,
        "memory_usage": payload.memory_usage,
        "latency_ms": payload.latency_ms,
        "request_count": payload.request_count,
        "error_rate": payload.error_rate,
    }

    for metric, value in metrics.items():
        db.add(
            Evidence(
                incident_id=incident_id,
                evidence_type=f"METRIC_{metric.upper()}",
                details=json.dumps({
                    "metric": metric,
                    "value": value,
                    "observed_at": now.isoformat(),
                }),
            )
        )

    db.add(
        Evidence(
            incident_id=incident_id,
            evidence_type="DETECTION_RESULT",
            details=json.dumps({
                **detection,
                "reason": reason,
                "ml_observations": count,
            }),
        )
    )

    db.add(
        TimelineEvent(
            incident_id=incident_id,
            timestamp=now,
            event_type="METRIC",
            description=(
                f"{reason}. Severity: {severity}. "
                f"ML score: {detection['decision_score']}."
            ),
        )
    )

    return incident_id, severity


@router.get("/status")
def telemetry_status():
    return {
        "system": "NEXUS AI",
        "component": "Persistent Telemetry Detection",
        "status": "ready",
        "detection_engine": "Isolation Forest + Thresholds",
        "model_loaded": get_detector.cache_info().currsize > 0,
        "observation_storage": "sqlite",
        "ml_observations_required": ML_OBSERVATIONS_REQUIRED,
        "observation_window_seconds": OBSERVATION_WINDOW_SECONDS,
        "duplicate_cooldown_minutes": COOLDOWN_MINUTES,
    }


@router.get("/history")
def telemetry_history(
    service: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(TelemetrySample)

    if service:
        query = query.filter(
            TelemetrySample.service == service
        )

    samples = (
        query.order_by(TelemetrySample.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(samples),
        "samples": [
            {
                "id": sample.id,
                "service": sample.service,
                "observed_at": sample.observed_at,
                "cpu_usage": sample.cpu_usage,
                "memory_usage": sample.memory_usage,
                "latency_ms": sample.latency_ms,
                "request_count": sample.request_count,
                "error_rate": sample.error_rate,
                "model_anomaly": sample.model_anomaly,
                "threshold_anomaly": sample.threshold_anomaly,
                "decision_score": sample.decision_score,
                "status": sample.status,
                "incident_id": sample.incident_id,
            }
            for sample in samples
        ],
    }


@router.post("/ingest")
def ingest_telemetry(
    payload: TelemetryInput,
    db: Session = Depends(get_db),
):
    service = payload.service.strip()

    if len(service) < 2:
        raise HTTPException(
            status_code=422,
            detail="Invalid service name",
        )

    payload.service = service

    try:
        detection = detect(payload)
    except (FileNotFoundError, ValueError, KeyError) as error:
        raise HTTPException(
            status_code=503,
            detail=f"Detection engine unavailable: {error}",
        )

    # Serialize read-check-write transactions in SQLite.
    # Must be the first DB statement in this session.
    try:
        db.execute(text("BEGIN IMMEDIATE"))

        now = datetime.utcnow()

        sample = TelemetrySample(
            service=service,
            observed_at=now,
            cpu_usage=payload.cpu_usage,
            memory_usage=payload.memory_usage,
            latency_ms=payload.latency_ms,
            request_count=payload.request_count,
            error_rate=payload.error_rate,
            model_anomaly=detection["model_anomaly"],
            threshold_anomaly=detection["threshold_anomaly"],
            decision_score=detection["decision_score"],
            status="RECEIVED",
        )

        db.add(sample)
        db.flush()

        status = "NORMAL"
        incident_id = None
        severity = None
        count = 0
        created = False

        if not detection["is_anomaly"]:
            status = "NORMAL"

        else:
            existing = recent_incident(db, service, now)

            if existing:
                status = "DUPLICATE_SUPPRESSED"
                incident_id = existing.id

            elif detection["threshold_anomaly"]:
                incident_id, severity = make_incident(
                    db, payload, detection, 0, now
                )
                status = "INCIDENT_CREATED"
                created = True

            else:
                count = consecutive_anomaly_count(
                    db, service, now
                )

                if count < ML_OBSERVATIONS_REQUIRED:
                    status = "OBSERVING"
                else:
                    incident_id, severity = make_incident(
                        db, payload, detection, count, now
                    )
                    status = "INCIDENT_CREATED"
                    created = True

        sample.status = status
        sample.incident_id = incident_id

        db.commit()

        return {
            "status": status,
            "service": service,
            "is_anomaly": detection["is_anomaly"],
            "incident_created": created,
            "incident_id": incident_id,
            "severity": severity,
            "observations": count,
            "required_observations": ML_OBSERVATIONS_REQUIRED,
            "detection": detection,
            "telemetry_id": sample.id,
        }

    except OperationalError as error:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=f"Database temporarily unavailable: {error}",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Telemetry processing failed",
        )

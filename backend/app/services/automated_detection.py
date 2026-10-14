
"""
NEXUS AI - Automated Incident Detection
Phase 4: Synthetic telemetry pipeline

Uses:
- Existing Isolation Forest detector
- Existing incident severity engine
- Existing evidence collector
- Existing timeline engine
- Existing SQLite database

No OpenAI API calls.
No deletion or modification of existing incidents.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from ml.anomaly_detection.detector import AnomalyDetector
from backend.incident.engine import IncidentEngine
from backend.evidence.collector import EvidenceCollector
from backend.timeline.engine import TimelineEngine

from backend.app.core.database import SessionLocal
from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent

# Import workflow models so existing relationships remain registered.
from backend.app.models.workflow import (
    RemediationWorkflow,
    WorkflowAuditEvent,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


def to_datetime(value):
    """Convert pandas or string timestamps into naive UTC datetimes."""

    if value is None:
        return None

    timestamp = pd.to_datetime(value, utc=True, errors="coerce")

    if pd.isna(timestamp):
        return None

    return timestamp.tz_localize(None).to_pydatetime()


def new_incident_id(db):
    """Generate a unique ID without using the old INC-1001 counter."""

    while True:
        incident_id = f"INC-AUTO-{uuid.uuid4().hex[:12].upper()}"

        if db.get(Incident, incident_id) is None:
            return incident_id


def build_root_cause_summary(incident, evidence):
    """
    Generate a transparent rule-based investigation summary.

    This is not an LLM diagnosis or a confirmed root cause.
    """

    observations = []

    if evidence["max_cpu"] >= 80:
        observations.append(
            f"elevated CPU usage ({evidence['max_cpu']:.1f}%)"
        )

    if evidence["max_memory"] >= 85:
        observations.append(
            f"elevated memory usage ({evidence['max_memory']:.1f}%)"
        )

    if evidence["max_latency"] >= 1000:
        observations.append(
            f"high request latency ({evidence['max_latency']:.1f} ms)"
        )

    if evidence["max_error_rate"] >= 15:
        observations.append(
            f"high error rate ({evidence['max_error_rate']:.1f}%)"
        )

    if evidence["database_logs"] > 0:
        observations.append(
            f"{evidence['database_logs']} database-related log records"
        )

    if not observations:
        observations.append(
            "anomalous metric patterns detected by Isolation Forest"
        )

    description = "; ".join(observations)

    return (
        f"Automated investigation for {incident.service}: "
        f"{description}. "
        "The underlying root cause is not yet confirmed. "
        "Human investigation is recommended."
    )


def run_automated_detection():
    print("\n" + "=" * 60)
    print("NEXUS AI - AUTOMATED INCIDENT DETECTION")
    print("=" * 60)

    normal_path = DATA_DIR / "normal_metrics.csv"
    incident_path = DATA_DIR / "incident_db_failure.csv"
    logs_path = DATA_DIR / "incident_logs.csv"

    for path in (normal_path, incident_path, logs_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Required telemetry file not found: {path}"
            )

    print("\n[1/7] Loading telemetry datasets...")

    normal_metrics = pd.read_csv(normal_path)
    incident_metrics = pd.read_csv(incident_path)
    incident_logs = pd.read_csv(logs_path)

    print(f"Normal records: {len(normal_metrics)}")
    print(f"Incident telemetry records: {len(incident_metrics)}")
    print(f"Log records: {len(incident_logs)}")

    print("\n[2/7] Training Isolation Forest...")

    detector = AnomalyDetector()
    detector.train(normal_metrics)

    print("Model trained successfully.")

    print("\n[3/7] Detecting anomalous telemetry...")

    detection_results = detector.predict(incident_metrics)

    anomalies = detection_results[
        detection_results["is_anomaly"]
    ].copy()

    print(f"Detected anomalous records: {len(anomalies)}")

    if anomalies.empty:
        print("\nNo anomalies detected. No incident created.")
        return None

    print("\n[4/7] Generating incident classification...")

    incident_engine = IncidentEngine()
    detected = incident_engine.create_incident(anomalies)

    if detected is None:
        print("Incident engine did not generate an incident.")
        return None

    print(f"Affected service: {detected.service}")
    print(f"Severity: {detected.severity}")
    print(f"Anomaly count: {detected.anomaly_count}")

    print("\n[5/7] Collecting evidence and timeline...")

    collector = EvidenceCollector()

    evidence_data = collector.collect(
        detected,
        incident_metrics,
        incident_logs,
    )

    timeline_engine = TimelineEngine()

    timeline_data = timeline_engine.build_timeline(
        metrics=incident_metrics,
        logs=incident_logs,
        service=detected.service,
    )

    print(f"Evidence fields: {len(evidence_data)}")
    print(f"Timeline events: {len(timeline_data)}")

    print("\n[6/7] Saving results to SQLite...")

    db = SessionLocal()

    try:
        incident_id = new_incident_id(db)

        root_cause = build_root_cause_summary(
            detected,
            evidence_data,
        )

        # These inputs are synthetic historical data.
        # The incident detection time is the current processing time.
        db_incident = Incident(
            id=incident_id,
            service=str(detected.service),
            severity=str(detected.severity),
            status="NEW",
            detected_at=datetime.utcnow(),
            root_cause=root_cause,
            confidence=None,
        )

        db.add(db_incident)
        db.flush()

        # Store observed telemetry as evidence records.
        db.add(
            Evidence(
                incident_id=incident_id,
                evidence_type="ANOMALY_COUNT",
                details=str(detected.anomaly_count),
            )
        )

        for key, value in evidence_data.items():
            db.add(
                Evidence(
                    incident_id=incident_id,
                    evidence_type=str(key),
                    details=json.dumps(value, default=str),
                )
            )

        # Store timeline events for the investigation dashboard.
        for event in timeline_data:
            db.add(
                TimelineEvent(
                    incident_id=incident_id,
                    timestamp=to_datetime(
                        event.get("timestamp")
                    ),
                    event_type=str(
                        event.get("type", "GENERAL")
                    ),
                    description=str(
                        event.get(
                            "event",
                            event.get("description", "Telemetry event"),
                        )
                    ),
                )
            )

        # Commit all records together.
        db.commit()

        print(f"Incident saved: {incident_id}")

    except Exception:
        db.rollback()
        print("Database transaction rolled back.")
        raise

    finally:
        db.close()

    print("\n[7/7] Detection completed successfully.")
    print("-" * 60)
    print(f"Incident ID: {incident_id}")
    print(f"Service: {detected.service}")
    print(f"Severity: {detected.severity}")
    print("Approval status: PENDING (default)")
    print("Existing incidents: UNCHANGED")
    print("Existing audit history: UNCHANGED")
    print("-" * 60)

    return incident_id


if __name__ == "__main__":
    run_automated_detection()

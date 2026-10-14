import sys
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent


# ==========================================
# PROJECT ROOT
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ==========================================
# NEXUS COMPONENTS
# ==========================================

from ml.anomaly_detection.detector import AnomalyDetector
from backend.incident.engine import IncidentEngine
from backend.evidence.collector import EvidenceCollector
from backend.timeline.engine import TimelineEngine
from ai.investigator.llm_investigator import LLMInvestigator
from backend.reporting.report_engine import IncidentReportEngine


class IncidentService:

    def __init__(self, db: Session):

        self.db = db

        # ------------------------------------------
        # DATA FILES
        # ------------------------------------------

        self.normal_metrics_file = (
            PROJECT_ROOT
            / "data"
            / "synthetic"
            / "normal_metrics.csv"
        )

        self.incident_metrics_file = (
            PROJECT_ROOT
            / "data"
            / "synthetic"
            / "incident_db_failure.csv"
        )

        self.incident_logs_file = (
            PROJECT_ROOT
            / "data"
            / "synthetic"
            / "incident_logs.csv"
        )

    # ==========================================
    # HELPER: CONVERT DATETIME
    # ==========================================

    @staticmethod
    def _to_datetime(value):

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        if isinstance(value, str):

            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).replace(tzinfo=None)

            except ValueError:
                return None

        return None

    # ==========================================
    # MAIN INCIDENT ANALYSIS PIPELINE
    # ==========================================

    def analyze_current_environment(self):

        # ------------------------------------------
        # 1. LOAD DATA
        # ------------------------------------------

        normal_metrics = pd.read_csv(
            self.normal_metrics_file
        )

        incident_metrics = pd.read_csv(
            self.incident_metrics_file
        )

        incident_logs = pd.read_csv(
            self.incident_logs_file
        )

        # ------------------------------------------
        # 2. ANOMALY DETECTION
        # ------------------------------------------

        detector = AnomalyDetector()

        detector.train(
            normal_metrics
        )

        detection_result = detector.predict(
            incident_metrics
        )

        anomalies = detection_result[
            detection_result["is_anomaly"]
        ]

        # ------------------------------------------
        # 3. INCIDENT ENGINE
        # ------------------------------------------

        incident_engine = IncidentEngine()

        incident = incident_engine.create_incident(
            anomalies
        )

        if incident is None:
            return None

        # ------------------------------------------
        # 4. EVIDENCE COLLECTION
        # ------------------------------------------

        evidence_collector = EvidenceCollector()

        evidence = evidence_collector.collect(
            incident,
            incident_metrics,
            incident_logs,
        )

        # ------------------------------------------
        # 5. TIMELINE
        # ------------------------------------------

        timeline_engine = TimelineEngine()

        timeline = timeline_engine.build_timeline(
            metrics=incident_metrics,
            logs=incident_logs,
            service=incident.service,
        )

        # ------------------------------------------
        # 6. AI INVESTIGATION
        # ------------------------------------------
        investigator = LLMInvestigator()

        investigation = investigator.investigate(
            evidence
        )

        # ------------------------------------------
        # 7. REPORT
        # ------------------------------------------

        report_engine = IncidentReportEngine()

        report = report_engine.generate(
            incident=incident,
            evidence=evidence,
            timeline=timeline,
            investigation=investigation,
        )

        # ==========================================
        # 8. SAVE INCIDENT
        # ==========================================

        incident_id = incident.incident_id

        existing_incident = self.db.get(
            Incident,
            incident_id
        )

        if existing_incident is None:

            root_cause = None
            confidence = None

            if isinstance(investigation, dict):

                root_cause = investigation.get(
                    "root_cause"
                )

                confidence = investigation.get(
                    "confidence"
                )

            detected_at = self._to_datetime(
                incident.detected_at
            )

            db_incident = Incident(
                id=incident_id,
                service=incident.service,
                severity=incident.severity,
                status=incident.status,
                detected_at=detected_at,
                root_cause=root_cause,
                confidence=confidence,
            )

            self.db.add(
                db_incident
            )

            self.db.commit()

        # ==========================================
        # 9. SAVE EVIDENCE
        # ==========================================

        existing_evidence = (
            self.db.query(Evidence)
            .filter(
                Evidence.incident_id == incident_id
            )
            .count()
        )

        if existing_evidence == 0:

            evidence_items = []

            if isinstance(evidence, dict):

                for key, value in evidence.items():

                    evidence_items.append(
                        Evidence(
                            incident_id=incident_id,
                            evidence_type=str(key),
                            details=json.dumps(
                                value,
                                default=str
                            ),
                        )
                    )

            elif isinstance(evidence, list):

                for index, item in enumerate(evidence):

                    evidence_items.append(
                        Evidence(
                            incident_id=incident_id,
                            evidence_type=f"EVIDENCE_{index + 1}",
                            details=json.dumps(
                                item,
                                default=str
                            ),
                        )
                    )

            elif evidence is not None:

                evidence_items.append(
                    Evidence(
                        incident_id=incident_id,
                        evidence_type="GENERAL",
                        details=json.dumps(
                            evidence,
                            default=str
                        ),
                    )
                )

            if evidence_items:

                self.db.add_all(
                    evidence_items
                )

                self.db.commit()

        # ==========================================
        # 10. SAVE TIMELINE
        # ==========================================

        existing_timeline = (
            self.db.query(TimelineEvent)
            .filter(
                TimelineEvent.incident_id == incident_id
            )
            .count()
        )

        if existing_timeline == 0:

            timeline_items = []

            if isinstance(timeline, list):

                for index, event in enumerate(timeline):

                    timestamp = None
                    event_type = f"EVENT_{index + 1}"
                    description = str(event)

                    if isinstance(event, dict):

                        timestamp = self._to_datetime(
                            event.get("timestamp")
                        )

                        event_type = str(
                            event.get(
                                "event_type",
                                event.get(
                                    "type",
                                    f"EVENT_{index + 1}"
                                )
                            )
                        )

                        description = str(
                            event.get(
                                "event",
                                event.get("description", event)
                            )
                        )

                    timeline_items.append(
                        TimelineEvent(
                            incident_id=incident_id,
                            timestamp=timestamp,
                            event_type=event_type,
                            description=description,
                        )
                    )
            elif timeline is not None:

                timeline_items.append(
                    TimelineEvent(
                        incident_id=incident_id,
                        timestamp=None,
                        event_type="GENERAL",
                        description=json.dumps(
                            timeline,
                            default=str
                        ),
                    )
                )

            if timeline_items:

                self.db.add_all(
                    timeline_items
                )

                self.db.commit()

        # ==========================================
        # 11. RETURN REPORT
        # ==========================================

        return report



import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from ml.anomaly_detection.detector import AnomalyDetector
from backend.incident.engine import IncidentEngine
from backend.evidence.collector import EvidenceCollector
from backend.timeline.engine import TimelineEngine
from backend.reporting.report_engine import IncidentReportEngine
from ai.investigator.investigator import AIInvestigator


NORMAL_METRICS = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "normal_metrics.csv"
)

INCIDENT_METRICS = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "incident_db_failure.csv"
)

INCIDENT_LOGS = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "incident_logs.csv"
)


def main():

    print("\n")
    print("==============================================")
    print("              NEXUS AI PLATFORM")
    print("          FULL PIPELINE TEST")
    print("==============================================")

    # ==========================================
    # STEP 1 — LOAD DATA
    # ==========================================

    print("\n[1/6] Loading data...")

    normal_metrics = pd.read_csv(
        NORMAL_METRICS
    )

    incident_metrics = pd.read_csv(
        INCIDENT_METRICS
    )

    incident_logs = pd.read_csv(
        INCIDENT_LOGS
    )

    print(
        f"Normal metrics    : {len(normal_metrics)}"
    )

    print(
        f"Incident metrics  : {len(incident_metrics)}"
    )

    print(
        f"Incident logs     : {len(incident_logs)}"
    )

    # ==========================================
    # STEP 2 — ANOMALY DETECTION
    # ==========================================

    print("\n[2/6] Running anomaly detection...")

    detector = AnomalyDetector()

    detector.train(
        normal_metrics
    )

    result = detector.predict(
        incident_metrics
    )

    anomalies = result[
        result["is_anomaly"]
    ]

    print(
        f"Anomalies detected: {len(anomalies)}"
    )

    # ==========================================
    # STEP 3 — INCIDENT CREATION
    # ==========================================

    print("\n[3/6] Creating incident...")

    incident_engine = IncidentEngine()

    incident = incident_engine.create_incident(
        anomalies
    )

    if incident is None:

        print("No incident detected.")
        return

    print(
        f"Incident ID : {incident.incident_id}"
    )

    print(
        f"Service     : {incident.service}"
    )

    print(
        f"Severity    : {incident.severity}"
    )

    # ==========================================
    # STEP 4 — EVIDENCE
    # ==========================================

    print("\n[4/6] Collecting evidence...")

    evidence_collector = EvidenceCollector()

    evidence = evidence_collector.collect(
        incident,
        incident_metrics,
        incident_logs,
    )

    print(
        f"Error logs    : {evidence['error_logs']}"
    )

    print(
        f"Database logs : {evidence['database_logs']}"
    )

    # ==========================================
    # STEP 5 — TIMELINE
    # ==========================================

    print("\n[5/6] Building timeline...")

    timeline_engine = TimelineEngine()

    timeline = timeline_engine.build_timeline(
        metrics=incident_metrics,
        logs=incident_logs,
        service=incident.service,
    )

    print(
        f"Timeline events: {len(timeline)}"
    )

    # ==========================================
    # STEP 6 — INVESTIGATION
    # ==========================================

    print("\n[6/6] Investigating incident...")

    investigator = AIInvestigator()

    investigation = investigator.investigate(
        evidence
    )

    # ==========================================
    # REPORT
    # ==========================================

    report_engine = IncidentReportEngine()

    report = report_engine.generate(
        incident=incident,
        evidence=evidence,
        timeline=timeline,
        investigation=investigation,
    )

    # ==========================================
    # FINAL REPORT
    # ==========================================

    print("\n")
    print("==============================================")
    print("             NEXUS INCIDENT REPORT")
    print("==============================================")

    print("\nINCIDENT")
    print("----------------------------------------------")

    print(
        f"ID       : {report['incident']['id']}"
    )

    print(
        f"Service  : {report['incident']['service']}"
    )

    print(
        f"Severity : {report['incident']['severity']}"
    )

    print(
        f"Status   : {report['incident']['status']}"
    )

    print("\nMETRICS")
    print("----------------------------------------------")

    print(
        f"CPU        : "
        f"{report['metrics']['max_cpu']}%"
    )

    print(
        f"Memory     : "
        f"{report['metrics']['max_memory']}%"
    )

    print(
        f"Latency    : "
        f"{report['metrics']['max_latency']} ms"
    )

    print(
        f"Error Rate : "
        f"{report['metrics']['max_error_rate']}%"
    )

    print("\nEVIDENCE")
    print("----------------------------------------------")

    print(
        f"Error Logs    : "
        f"{report['evidence']['error_logs']}"
    )

    print(
        f"Database Logs : "
        f"{report['evidence']['database_logs']}"
    )

    print("\nROOT CAUSE ANALYSIS")
    print("----------------------------------------------")

    print(
        report["investigation"]["root_cause"]
    )

    print(
        f"\nConfidence: "
        f"{report['investigation']['confidence']}"
    )

    print("\nRECOMMENDED ACTIONS")
    print("----------------------------------------------")

    for action in report[
        "investigation"
    ]["recommendations"]:

        print(f"- {action}")

    print("\nTIMELINE")
    print("----------------------------------------------")

    for event in timeline[:15]:

        print(
            f"{event['timestamp']} | "
            f"{event['severity']} | "
            f"{event['event']}"
        )

    print("\n==============================================")
    print("        NEXUS PIPELINE COMPLETE 🚀")
    print("==============================================")


if __name__ == "__main__":
    main()
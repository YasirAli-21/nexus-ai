import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from ml.anomaly_detection.detector import AnomalyDetector
from backend.incident.engine import IncidentEngine
from backend.evidence.collector import EvidenceCollector
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

    print("\n==============================")
    print("       NEXUS AI INVESTIGATOR")
    print("==============================")

    # Load data
    normal_metrics = pd.read_csv(NORMAL_METRICS)
    incident_metrics = pd.read_csv(INCIDENT_METRICS)
    incident_logs = pd.read_csv(INCIDENT_LOGS)

    # ML detection
    detector = AnomalyDetector()

    detector.train(normal_metrics)

    result = detector.predict(
        incident_metrics
    )

    anomalies = result[
        result["is_anomaly"]
    ]

    # Incident creation
    incident_engine = IncidentEngine()

    incident = incident_engine.create_incident(
        anomalies
    )

    if incident is None:
        print("No incident detected.")
        return

    # Evidence collection
    collector = EvidenceCollector()

    evidence = collector.collect(
        incident,
        incident_metrics,
        incident_logs,
    )

    # AI Investigation
    investigator = AIInvestigator()

    analysis = investigator.investigate(
        evidence
    )

    # Display
    print("\n==============================")
    print("          INCIDENT")
    print("==============================")

    print(f"ID       : {incident.incident_id}")
    print(f"Service  : {incident.service}")
    print(f"Severity : {incident.severity}")

    print("\n==============================")
    print("       AI INVESTIGATION")
    print("==============================")

    print("\nFindings:")

    for finding in analysis["findings"]:
        print(f"- {finding}")

    print("\nRoot Cause:")
    print(analysis["root_cause"])

    print("\nConfidence:")
    print(analysis["confidence"])

    print("\nRecommended Actions:")

    for recommendation in analysis[
        "recommendations"
    ]:
        print(f"- {recommendation}")

    print("\n==============================")
    print("     INVESTIGATION COMPLETE")
    print("==============================")


if __name__ == "__main__":
    main()
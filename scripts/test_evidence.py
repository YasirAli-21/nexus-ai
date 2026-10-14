import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from ml.anomaly_detection.detector import AnomalyDetector
from backend.incident.engine import IncidentEngine
from backend.evidence.collector import EvidenceCollector


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
    print("       NEXUS EVIDENCE ENGINE")
    print("==============================")

    normal_metrics = pd.read_csv(NORMAL_METRICS)
    incident_metrics = pd.read_csv(INCIDENT_METRICS)
    incident_logs = pd.read_csv(INCIDENT_LOGS)

    # Detect anomalies
    detector = AnomalyDetector()
    detector.train(normal_metrics)

    result = detector.predict(incident_metrics)

    anomalies = result[
        result["is_anomaly"]
    ]

    # Create incident
    incident_engine = IncidentEngine()

    incident = incident_engine.create_incident(
        anomalies
    )

    if incident is None:
        print("No incident found.")
        return

    # Collect evidence
    collector = EvidenceCollector()

    evidence = collector.collect(
        incident,
        incident_metrics,
        incident_logs,
    )

    print("\n==============================")
    print("       INCIDENT")
    print("==============================")

    print(f"ID       : {incident.incident_id}")
    print(f"Service  : {incident.service}")
    print(f"Severity : {incident.severity}")

    print("\n==============================")
    print("       CORRELATED EVIDENCE")
    print("==============================")

    print(f"Metric records : {evidence['metric_records']}")
    print(f"Error logs     : {evidence['error_logs']}")
    print(f"Database logs  : {evidence['database_logs']}")

    print("\nMetric Evidence")
    print("------------------------------")

    print(f"Max CPU        : {evidence['max_cpu']}%")
    print(f"Max Memory     : {evidence['max_memory']}%")
    print(f"Max Latency    : {evidence['max_latency']} ms")
    print(f"Max Error Rate : {evidence['max_error_rate']}%")

    print("\nDatabase Evidence")
    print("------------------------------")

    for message, count in evidence[
        "database_messages"
    ].items():

        print(f"{message}: {count}")

    print("\n==============================")
    print("    EVIDENCE COLLECTION DONE")
    print("==============================")


if __name__ == "__main__":
    main()
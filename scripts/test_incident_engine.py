import sys
from pathlib import Path

import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from ml.anomaly_detection.detector import AnomalyDetector
from backend.incident.engine import IncidentEngine


NORMAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "normal_metrics.csv"
)

INCIDENT_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "incident_db_failure.csv"
)


def main():

    print("\n==============================")
    print("      NEXUS INCIDENT ENGINE")
    print("==============================")

    # Load data
    normal_data = pd.read_csv(NORMAL_FILE)
    incident_data = pd.read_csv(INCIDENT_FILE)

    print("\nLoading datasets...")
    print(f"Normal records   : {len(normal_data)}")
    print(f"Test records     : {len(incident_data)}")

    # Train detector
    detector = AnomalyDetector()

    print("\nTraining anomaly detector...")
    detector.train(normal_data)

    # Detect anomalies
    print("Detecting anomalies...")

    result = detector.predict(incident_data)

    anomalies = result[
        result["is_anomaly"]
    ]

    print(f"Anomalies detected: {len(anomalies)}")

    # Incident Engine
    engine = IncidentEngine()

    print("\nCreating incident...")

    incident = engine.create_incident(anomalies)

    if incident is None:

        print("\nNo incident created.")
        return

    print("\n==============================")
    print("      🔴 INCIDENT CREATED")
    print("==============================")

    print(f"ID             : {incident.incident_id}")
    print(f"Service        : {incident.service}")
    print(f"Severity       : {incident.severity}")
    print(f"Detected       : {incident.detected_at}")
    print(f"Status         : {incident.status}")

    print("\nIncident Evidence")
    print("------------------------------")

    print(f"Anomalies      : {incident.anomaly_count}")
    print(f"Max CPU        : {incident.cpu_usage}%")
    print(f"Max Memory     : {incident.memory_usage}%")
    print(f"Max Latency    : {incident.latency_ms} ms")
    print(f"Max Error Rate : {incident.error_rate}%")

    print("\nDescription")
    print("------------------------------")
    print(incident.description)

    print("\n==============================")
    print("   INCIDENT ENGINE COMPLETE")
    print("==============================")


if __name__ == "__main__":
    main()
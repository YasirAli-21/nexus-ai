import sys
from pathlib import Path

import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from ml.anomaly_detection.detector import AnomalyDetector


NORMAL_FILE = PROJECT_ROOT / "data" / "synthetic" / "normal_metrics.csv"
INCIDENT_FILE = PROJECT_ROOT / "data" / "synthetic" / "incident_db_failure.csv"


def main():
    print("\n==============================")
    print("       NEXUS AI DETECTOR")
    print("==============================")

    # Check input files
    if not NORMAL_FILE.exists():
        print(f"\nERROR: Normal data not found:")
        print(NORMAL_FILE)
        return

    if not INCIDENT_FILE.exists():
        print(f"\nERROR: Incident data not found:")
        print(INCIDENT_FILE)
        return

    # Load datasets
    print("\nLoading datasets...")

    normal_data = pd.read_csv(NORMAL_FILE)
    incident_data = pd.read_csv(INCIDENT_FILE)

    print(f"Normal records: {len(normal_data)}")
    print(f"Incident test records: {len(incident_data)}")

    # Create detector
    detector = AnomalyDetector()

    # Train using normal behavior
    print("\nTraining anomaly detection model...")
    detector.train(normal_data)

    print("Model trained successfully.")

    # Detect anomalies
    print("\nAnalyzing incident data...")

    result = detector.predict(incident_data)

    anomalies = result[result["is_anomaly"]]

    # Results
    print("\n==============================")
    print("       DETECTION RESULT")
    print("==============================")

    print(f"Total records analyzed : {len(result)}")
    print(f"Anomalies detected     : {len(anomalies)}")

    if len(anomalies) > 0:

        print("\n🚨 ANOMALOUS RECORDS:")
        print("-" * 80)

        print(
            anomalies[
                [
                    "timestamp",
                    "service",
                    "cpu_usage",
                    "memory_usage",
                    "latency_ms",
                    "error_rate",
                ]
            ].tail(10).to_string(index=False)
        )

    else:
        print("\nNo anomalies detected.")

    print("\n==============================")
    print("       NEXUS TEST COMPLETE")
    print("==============================")


if __name__ == "__main__":
    main()
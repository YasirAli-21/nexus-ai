import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.timeline.engine import TimelineEngine


METRICS_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "incident_db_failure.csv"
)

LOGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "incident_logs.csv"
)


def main():

    print("\n==============================")
    print("       NEXUS TIMELINE")
    print("==============================")

    metrics = pd.read_csv(METRICS_FILE)
    logs = pd.read_csv(LOGS_FILE)

    engine = TimelineEngine()

    timeline = engine.build_timeline(
        metrics=metrics,
        logs=logs,
        service="payment-service",
    )

    print(
        f"\nTimeline events generated: "
        f"{len(timeline)}"
    )

    print("\n==============================")
    print("       INCIDENT TIMELINE")
    print("==============================")

    # Show first 30 events
    for event in timeline[:30]:

        print(
            f"{event['timestamp']} | "
            f"{event['severity']:8} | "
            f"{event['type']:6} | "
            f"{event['event']}"
        )

    print("\n==============================")
    print("      TIMELINE COMPLETE")
    print("==============================")


if __name__ == "__main__":
    main()
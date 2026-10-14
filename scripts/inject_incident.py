from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/synthetic/normal_metrics.csv")
OUTPUT_FILE = Path("data/synthetic/incident_db_failure.csv")


def inject_database_failure():
    df = pd.read_csv(INPUT_FILE)

    # Select payment-service records
    payment_mask = df["service"] == "payment-service"

    payment_indices = df[payment_mask].index

    # Inject incident into the final 50 payment records
    incident_indices = payment_indices[-50:]

    # Simulate database connection exhaustion
    df.loc[incident_indices, "cpu_usage"] = 90
    df.loc[incident_indices, "memory_usage"] = 88
    df.loc[incident_indices, "latency_ms"] = 2400
    df.loc[incident_indices, "request_count"] = 180
    df.loc[incident_indices, "error_rate"] = 38

    df.to_csv(OUTPUT_FILE, index=False)

    print("Database failure incident injected.")
    print(f"Incident records: {len(incident_indices)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    inject_database_failure()
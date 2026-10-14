from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/synthetic/normal_logs.csv")
OUTPUT_FILE = Path("data/synthetic/incident_logs.csv")


def inject_incident_logs():
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)

    payment_mask = df["service"] == "payment-service"
    payment_indices = df[payment_mask].index

    # Last 50 payment logs represent the incident period
    incident_indices = payment_indices[-50:]

    error_messages = [
        "Database connection failed",
        "Database connection timeout",
        "Connection pool exhausted",
        "Unable to acquire database connection",
        "Payment transaction failed due to database error",
    ]

    for i, index in enumerate(incident_indices):
        df.loc[index, "level"] = "ERROR"
        df.loc[index, "message"] = error_messages[
            i % len(error_messages)
        ]

    df.to_csv(OUTPUT_FILE, index=False)

    print("Database incident logs injected.")
    print(f"Incident log records: {len(incident_indices)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    inject_incident_logs()
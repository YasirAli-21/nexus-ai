import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


SERVICES = [
    "user-service",
    "product-service",
    "order-service",
    "payment-service",
]

NORMAL_MESSAGES = {
    "user-service": [
        "User authenticated successfully",
        "User profile retrieved",
        "User request processed",
    ],
    "product-service": [
        "Product retrieved successfully",
        "Product search completed",
        "Inventory checked",
    ],
    "order-service": [
        "Order created successfully",
        "Order status updated",
        "Order retrieved successfully",
    ],
    "payment-service": [
        "Payment request received",
        "Payment processed successfully",
        "Payment verification completed",
    ],
}


def generate_logs(rows_per_service=500):
    logs = []

    start_time = datetime.now() - timedelta(hours=5)

    for service in SERVICES:
        for i in range(rows_per_service):
            timestamp = start_time + timedelta(minutes=i)

            logs.append({
                "timestamp": timestamp,
                "service": service,
                "level": "INFO",
                "message": random.choice(NORMAL_MESSAGES[service]),
            })

    return pd.DataFrame(logs)


def main():
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    logs = generate_logs()

    output_file = output_dir / "normal_logs.csv"
    logs.to_csv(output_file, index=False)

    print(f"Generated {len(logs)} log records.")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
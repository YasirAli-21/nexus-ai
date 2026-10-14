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


def generate_metrics(rows_per_service=500):
    data = []

    start_time = datetime.now() - timedelta(hours=5)

    for service in SERVICES:
        for i in range(rows_per_service):
            timestamp = start_time + timedelta(minutes=i)

            cpu = random.uniform(25, 65)
            memory = random.uniform(35, 70)
            latency = random.uniform(100, 400)
            request_count = random.randint(50, 200)
            error_rate = random.uniform(0, 3)

            data.append({
                "timestamp": timestamp,
                "service": service,
                "cpu_usage": round(cpu, 2),
                "memory_usage": round(memory, 2),
                "latency_ms": round(latency, 2),
                "request_count": request_count,
                "error_rate": round(error_rate, 2),
            })

    return pd.DataFrame(data)


def main():
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = generate_metrics()

    output_file = output_dir / "normal_metrics.csv"
    metrics.to_csv(output_file, index=False)

    print(f"Generated {len(metrics)} metric records.")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
    
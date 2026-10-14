from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class Incident:
    incident_id: str
    service: str
    severity: str
    detected_at: str
    status: str
    anomaly_count: int
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    error_rate: float
    description: str


class IncidentEngine:

    def __init__(self):
        self.incident_counter = 1000

    def _generate_incident_id(self):
        self.incident_counter += 1
        return f"INC-{self.incident_counter}"

    def calculate_severity(self, data: pd.DataFrame) -> str:
        """
        Determine incident severity using abnormal metrics.
        """

        max_cpu = data["cpu_usage"].max()
        max_memory = data["memory_usage"].max()
        max_latency = data["latency_ms"].max()
        max_error_rate = data["error_rate"].max()

        # Critical conditions
        if (
            max_error_rate >= 30
            or max_latency >= 2000
            or max_cpu >= 90
        ):
            return "CRITICAL"

        # High conditions
        if (
            max_error_rate >= 15
            or max_latency >= 1000
            or max_cpu >= 80
        ):
            return "HIGH"

        # Medium conditions
        if (
            max_error_rate >= 5
            or max_latency >= 700
            or max_cpu >= 70
        ):
            return "MEDIUM"

        return "LOW"

    def create_incident(
        self,
        anomalous_data: pd.DataFrame
    ) -> Optional[Incident]:

        if anomalous_data.empty:
            return None

        # Find the service responsible for most anomalies
        service_counts = anomalous_data["service"].value_counts()

        service = service_counts.index[0]

        service_data = anomalous_data[
            anomalous_data["service"] == service
        ]

        severity = self.calculate_severity(service_data)

        incident_id = self._generate_incident_id()

        detected_at = str(
            service_data["timestamp"].min()
        )

        description = (
            f"Multiple abnormal metrics detected in "
            f"{service}. "
            f"Potential service-level incident requiring investigation."
        )

        incident = Incident(
            incident_id=incident_id,
            service=service,
            severity=severity,
            detected_at=detected_at,
            status="NEW",
            anomaly_count=len(service_data),
            cpu_usage=float(service_data["cpu_usage"].max()),
            memory_usage=float(service_data["memory_usage"].max()),
            latency_ms=float(service_data["latency_ms"].max()),
            error_rate=float(service_data["error_rate"].max()),
            description=description,
        )

        return incident
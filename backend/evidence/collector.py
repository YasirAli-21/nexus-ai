import pandas as pd


class EvidenceCollector:

    def collect(
        self,
        incident,
        metrics: pd.DataFrame,
        logs: pd.DataFrame,
    ):

        service = incident.service

        # Metrics belonging to affected service
        service_metrics = metrics[
            metrics["service"] == service
        ]

        # Logs belonging to affected service
        service_logs = logs[
            logs["service"] == service
        ]

        # Error logs
        error_logs = service_logs[
            service_logs["level"] == "ERROR"
        ]

        # Database-related logs
        database_logs = service_logs[
            service_logs["message"].str.contains(
                "database|connection|pool",
                case=False,
                na=False,
            )
        ]

        evidence = {
            "service": service,
            "metric_records": len(service_metrics),
            "error_logs": len(error_logs),
            "database_logs": len(database_logs),
            "max_cpu": float(
                service_metrics["cpu_usage"].max()
            ),
            "max_memory": float(
                service_metrics["memory_usage"].max()
            ),
            "max_latency": float(
                service_metrics["latency_ms"].max()
            ),
            "max_error_rate": float(
                service_metrics["error_rate"].max()
            ),
            "database_messages": (
                database_logs["message"]
                .value_counts()
                .to_dict()
            ),
        }

        return evidence
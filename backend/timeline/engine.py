import pandas as pd


class TimelineEngine:

    def build_timeline(
        self,
        metrics: pd.DataFrame,
        logs: pd.DataFrame,
        service: str,
    ):

        timeline = []

        service_metrics = metrics[
            metrics["service"] == service
        ].copy()

        service_logs = logs[
            logs["service"] == service
        ].copy()

        # Make sure timestamps are datetime
        service_metrics["timestamp"] = pd.to_datetime(
            service_metrics["timestamp"]
        )

        service_logs["timestamp"] = pd.to_datetime(
            service_logs["timestamp"]
        )

        # -----------------------------
        # METRIC EVENTS
        # -----------------------------

        for _, row in service_metrics.iterrows():

            timestamp = row["timestamp"]

            if row["cpu_usage"] >= 85:
                timeline.append({
                    "timestamp": timestamp,
                    "type": "METRIC",
                    "severity": "HIGH",
                    "event": (
                        f"CPU utilization reached "
                        f"{row['cpu_usage']}%"
                    ),
                })

            if row["memory_usage"] >= 85:
                timeline.append({
                    "timestamp": timestamp,
                    "type": "METRIC",
                    "severity": "HIGH",
                    "event": (
                        f"Memory utilization reached "
                        f"{row['memory_usage']}%"
                    ),
                })

            if row["latency_ms"] >= 1500:
                timeline.append({
                    "timestamp": timestamp,
                    "type": "METRIC",
                    "severity": "HIGH",
                    "event": (
                        f"Latency increased to "
                        f"{row['latency_ms']} ms"
                    ),
                })

            if row["error_rate"] >= 20:
                timeline.append({
                    "timestamp": timestamp,
                    "type": "METRIC",
                    "severity": "CRITICAL",
                    "event": (
                        f"Error rate increased to "
                        f"{row['error_rate']}%"
                    ),
                })

        # -----------------------------
        # LOG EVENTS
        # -----------------------------

        for _, row in service_logs.iterrows():

            if str(row["level"]).upper() == "ERROR":

                timeline.append({
                    "timestamp": row["timestamp"],
                    "type": "LOG",
                    "severity": "CRITICAL",
                    "event": row["message"],
                })

        # -----------------------------
        # SORT TIMELINE
        # -----------------------------

        timeline.sort(
            key=lambda event: event["timestamp"]
        )

        return timeline
from datetime import datetime


class IncidentReportEngine:

    def generate(
        self,
        incident,
        evidence: dict,
        timeline: list,
        investigation: dict,
    ):

        report = {
            "report_generated_at": datetime.now().isoformat(),

            "incident": {
                "id": incident.incident_id,
                "service": incident.service,
                "severity": incident.severity,
                "status": incident.status,
                "detected_at": incident.detected_at,
            },

            "metrics": {
                "max_cpu": evidence["max_cpu"],
                "max_memory": evidence["max_memory"],
                "max_latency": evidence["max_latency"],
                "max_error_rate": evidence["max_error_rate"],
            },

            "evidence": {
                "metric_records": evidence["metric_records"],
                "error_logs": evidence["error_logs"],
                "database_logs": evidence["database_logs"],
                "database_messages": evidence[
                    "database_messages"
                ],
            },

            "timeline": timeline,

            "investigation": investigation,
        }

        return report
class AIInvestigator:

    def investigate(self, evidence: dict) -> dict:

        service = evidence["service"]

        cpu = evidence["max_cpu"]
        memory = evidence["max_memory"]
        latency = evidence["max_latency"]
        error_rate = evidence["max_error_rate"]

        database_logs = evidence["database_logs"]
        database_messages = evidence["database_messages"]

        findings = []

        # -----------------------------
        # METRIC ANALYSIS
        # -----------------------------

        if cpu >= 90:
            findings.append(
                "CPU utilization is critically high."
            )

        elif cpu >= 80:
            findings.append(
                "CPU utilization is significantly elevated."
            )

        if memory >= 85:
            findings.append(
                "Memory utilization is critically high."
            )

        elif memory >= 75:
            findings.append(
                "Memory utilization is elevated."
            )

        if latency >= 2000:
            findings.append(
                "Application latency is critically elevated."
            )

        elif latency >= 1000:
            findings.append(
                "Application latency is significantly elevated."
            )

        if error_rate >= 30:
            findings.append(
                "Application error rate is critically elevated."
            )

        elif error_rate >= 15:
            findings.append(
                "Application error rate is significantly elevated."
            )

        # -----------------------------
        # DATABASE ANALYSIS
        # -----------------------------

        database_failure = (
            database_logs > 0
            and any(
                (
                    "connection" in message.lower()
                    or "pool" in message.lower()
                    or "database" in message.lower()
                )
                for message in database_messages
            )
        )

        # -----------------------------
        # ROOT CAUSE
        # -----------------------------

        if database_failure:

            root_cause = (
                "The most likely root cause is a database "
                "connectivity or connection-pool failure "
                "affecting the service."
            )

            confidence = "HIGH"

        elif latency >= 2000 and error_rate >= 30:

            root_cause = (
                "The service is experiencing severe performance "
                "degradation and elevated failures, but the "
                "available evidence is insufficient to identify "
                "a specific root cause."
            )

            confidence = "MEDIUM"

        else:

            root_cause = (
                "An abnormal service condition was detected, "
                "but the available evidence is insufficient "
                "to determine the root cause."
            )

            confidence = "LOW"

        # -----------------------------
        # RECOMMENDATIONS
        # -----------------------------

        recommendations = []

        if database_failure:

            recommendations.extend([
                "Inspect database connection pool utilization.",
                "Check active database connections.",
                "Check database server health.",
                "Review recent application or database changes.",
                "Review database connection pool configuration.",
            ])

        if cpu >= 85:

            recommendations.append(
                "Inspect CPU-intensive processes and requests."
            )

        if memory >= 80:

            recommendations.append(
                "Inspect memory consumption and possible memory leaks."
            )

        if latency >= 1500:

            recommendations.append(
                "Identify slow requests and dependent services."
            )

        return {
            "service": service,
            "investigation_mode": "DETERMINISTIC_FALLBACK",
            "findings": findings,
            "root_cause": root_cause,
            "confidence": confidence,
            "recommendations": recommendations,
        }

"""
NEXUS AI - Phase 9
Read-only API smoke tests.

These tests:
- Use the running local backend
- Send GET requests only
- Do not create incidents
- Do not modify approval decisions
- Do not execute remediation
- Do not change the database

Run:
    python -m unittest discover -s tests -p "test_api_smoke.py" -v
"""

import json
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 10


def get_json(path):
    url = BASE_URL + path

    with urlopen(url, timeout=TIMEOUT) as response:
        status_code = response.status
        payload = json.loads(response.read().decode("utf-8"))

    return status_code, payload


class TestNexusAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            status, _ = get_json("/health")
            if status != 200:
                raise RuntimeError(
                    f"Backend health returned HTTP {status}"
                )
        except (URLError, HTTPError) as error:
            raise RuntimeError(
                "NEXUS AI backend is not running on "
                f"{BASE_URL}. Start Uvicorn first."
            ) from error

    def test_01_health_endpoint(self):
        status, data = get_json("/health")

        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "healthy")

    def test_02_incidents_endpoint(self):
        status, data = get_json("/api/incidents")

        self.assertEqual(status, 200)
        self.assertIn("count", data)
        self.assertIn("incidents", data)
        self.assertIsInstance(data["incidents"], list)
        self.assertEqual(
            data["count"],
            len(data["incidents"])
        )

    def test_03_incident_structure(self):
        _, data = get_json("/api/incidents")

        if not data["incidents"]:
            self.skipTest("No incidents available")

        incident = data["incidents"][0]

        for field in ("id", "service", "severity", "status"):
            self.assertIn(field, incident)

        self.assertTrue(incident["id"])
        self.assertTrue(incident["service"])

    def test_04_telemetry_status(self):
        status, data = get_json("/api/telemetry/status")

        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ready")
        self.assertEqual(
            data["observation_storage"],
            "sqlite"
        )

    def test_05_telemetry_history(self):
        status, data = get_json(
            "/api/telemetry/history?limit=10"
        )

        self.assertEqual(status, 200)
        self.assertIn("count", data)
        self.assertIn("samples", data)
        self.assertIsInstance(data["samples"], list)
        self.assertEqual(
            data["count"],
            len(data["samples"])
        )
        self.assertLessEqual(data["count"], 10)

    def test_06_investigation_routes_registered(self):
        status, data = get_json("/openapi.json")

        self.assertEqual(status, 200)

        paths = data["paths"]

        self.assertIn(
            "/api/incidents/{incident_id}/investigate",
            paths
        )

        self.assertIn(
            "/api/incidents/{incident_id}/investigation-report",
            paths
        )

    def test_07_saved_investigation_report(self):
        incident_id = "INC-LIVE-41EE1B2905DE"

        status, data = get_json(
            f"/api/incidents/{incident_id}/investigation-report"
        )

        self.assertEqual(status, 200)
        self.assertEqual(data["incident_id"], incident_id)
        self.assertEqual(data["status"], "AVAILABLE")

        report = data["report"]

        self.assertIsInstance(report, dict)
        self.assertIn("root_cause", report)
        self.assertIn("confidence", report)
        self.assertIn("findings", report)
        self.assertIn("recommendations", report)

    def test_08_workflow_endpoint(self):
        incident_id = "INC-1002"

        status, data = get_json(
            f"/api/incidents/{incident_id}/workflow"
        )

        self.assertEqual(status, 200)
        self.assertIn("approval_status", data)
        self.assertIn("remediation_status", data)
        self.assertIn("audit", data)

    def test_09_rejected_workflow_preserved(self):
        status, data = get_json(
            "/api/incidents/INC-1001/workflow"
        )

        self.assertEqual(status, 200)
        self.assertEqual(
            data["approval_status"],
            "REJECTED"
        )

    def test_10_approved_workflow_preserved(self):
        status, data = get_json(
            "/api/incidents/INC-1002/workflow"
        )

        self.assertEqual(status, 200)
        self.assertEqual(
            data["approval_status"],
            "APPROVED"
        )

    def test_11_unknown_incident_returns_404(self):
        try:
            get_json(
                "/api/incidents/INC-DOES-NOT-EXIST"
            )
        except HTTPError as error:
            self.assertEqual(error.code, 404)
        else:
            self.fail(
                "Expected HTTP 404 for unknown incident"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

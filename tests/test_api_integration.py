
"""
NEXUS AI - Phase 9
Isolated API integration tests.

Uses a temporary SQLite database.
Does NOT modify data/database/nexus.db.

Run:
python -m unittest discover -s tests -p "test_api_integration.py" -v
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.database import Base, get_db

# Import every database model before creating tables.
from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent
from backend.app.api.auth import require_auth
from backend.app.models.workflow import (
    RemediationWorkflow,
    WorkflowAuditEvent,
)
from backend.app.models.telemetry import TelemetrySample


class TestNexusIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory(
            prefix="nexus_test_"
        )

        cls.db_path = (
            Path(cls.temp_dir.name) / "integration_test.db"
        )

        cls.test_engine = create_engine(
            f"sqlite:///{cls.db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )

        Base.metadata.create_all(bind=cls.test_engine)

        cls.TestSession = sessionmaker(
            bind=cls.test_engine,
            autocommit=False,
            autoflush=False,
        )

        def override_get_db():
            db = cls.TestSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = lambda: True

        # No TestClient context manager:
        # this avoids running the application's startup
        # lifespan against the normal application engine.
        cls.client = TestClient(app)

        cls.seed_incidents()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        app.dependency_overrides.pop(get_db, None)
        cls.test_engine.dispose()
        cls.temp_dir.cleanup()

    @classmethod
    def seed_incidents(cls):
        db = cls.TestSession()

        try:
            for incident_id in (
                "TEST-APPROVE",
                "TEST-REJECT",
                "TEST-UNAPPROVED",
                "TEST-INVESTIGATE",
            ):
                db.add(
                    Incident(
                        id=incident_id,
                        service="integration-test-service",
                        severity="HIGH",
                        status="NEW",
                        detected_at=datetime.utcnow(),
                        root_cause=None,
                        confidence=None,
                    )
                )

            db.add(
                Evidence(
                    incident_id="TEST-INVESTIGATE",
                    evidence_type="METRIC_CPU_USAGE",
                    details='{"metric":"cpu_usage","value":96}',
                )
            )

            db.add(
                Evidence(
                    incident_id="TEST-INVESTIGATE",
                    evidence_type="METRIC_MEMORY_USAGE",
                    details='{"metric":"memory_usage","value":95}',
                )
            )

            db.add(
                Evidence(
                    incident_id="TEST-INVESTIGATE",
                    evidence_type="METRIC_LATENCY_MS",
                    details='{"metric":"latency_ms","value":3000}',
                )
            )

            db.add(
                Evidence(
                    incident_id="TEST-INVESTIGATE",
                    evidence_type="METRIC_ERROR_RATE",
                    details='{"metric":"error_rate","value":40}',
                )
            )

            db.commit()

        finally:
            db.close()

    def test_01_temp_database_is_isolated(self):
        self.assertTrue(self.db_path.exists())

        self.assertIn(
            "nexus_test_",
            str(self.db_path)
        )

        self.assertNotEqual(
            self.db_path.name,
            "nexus.db"
        )

        with self.TestSession() as db:
            count = db.query(Incident).count()

        self.assertEqual(count, 4)

    def test_02_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            "healthy"
        )

    def test_03_incident_listing(self):
        response = self.client.get("/api/incidents")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertGreaterEqual(data["count"], 4)

        ids = {
            item["id"] for item in data["incidents"]
        }

        self.assertIn("TEST-APPROVE", ids)
        self.assertIn("TEST-REJECT", ids)

    def test_04_ml_anomaly_confirmation(self):
        payload = {
            "service": "integration-ml-test",
            "cpu_usage": 25,
            "memory_usage": 35,
            "latency_ms": 110,
            "request_count": 300,
            "error_rate": 0.5,
        }

        statuses = []
        responses = []

        for _ in range(3):
            response = self.client.post(
                "/api/telemetry/ingest",
                json=payload,
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

            data = response.json()

            statuses.append(data["status"])
            responses.append(data)

        self.assertEqual(
            statuses,
            [
                "OBSERVING",
                "OBSERVING",
                "INCIDENT_CREATED",
            ],
        )

        incident_id = responses[2]["incident_id"]

        self.assertIsNotNone(incident_id)

        with self.TestSession() as db:
            samples = (
                db.query(TelemetrySample)
                .filter(
                    TelemetrySample.service ==
                    "integration-ml-test"
                )
                .all()
            )

            incident = db.get(Incident, incident_id)

        self.assertEqual(len(samples), 3)
        self.assertIsNotNone(incident)
        self.assertEqual(incident.severity, "LOW")

    def test_05_critical_incident_immediate(self):
        payload = {
            "service": "integration-critical-test",
            "cpu_usage": 97,
            "memory_usage": 96,
            "latency_ms": 3500,
            "request_count": 500,
            "error_rate": 42,
        }

        response = self.client.post(
            "/api/telemetry/ingest",
            json=payload,
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        data = response.json()

        self.assertEqual(
            data["status"],
            "INCIDENT_CREATED",
        )
        self.assertEqual(
            data["severity"],
            "CRITICAL",
        )

        incident_id = data["incident_id"]

        with self.TestSession() as db:
            incident = db.get(Incident, incident_id)

        self.assertIsNotNone(incident)

    def test_06_duplicate_suppression(self):
        payload = {
            "service": "integration-duplicate-test",
            "cpu_usage": 97,
            "memory_usage": 96,
            "latency_ms": 3500,
            "request_count": 500,
            "error_rate": 42,
        }

        first = self.client.post(
            "/api/telemetry/ingest",
            json=payload,
        )

        second = self.client.post(
            "/api/telemetry/ingest",
            json=payload,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        first_data = first.json()
        second_data = second.json()

        self.assertEqual(
            first_data["status"],
            "INCIDENT_CREATED",
        )

        self.assertEqual(
            second_data["status"],
            "DUPLICATE_SUPPRESSED",
        )

        self.assertEqual(
            first_data["incident_id"],
            second_data["incident_id"],
        )

        with self.TestSession() as db:
            matching = (
                db.query(Incident)
                .filter(
                    Incident.service ==
                    "integration-duplicate-test"
                )
                .count()
            )

        self.assertEqual(matching, 1)

    def test_07_invalid_telemetry_rejected(self):
        response = self.client.post(
            "/api/telemetry/ingest",
            json={
                "service": "invalid-test",
                "cpu_usage": 150,
                "memory_usage": 50,
                "latency_ms": 100,
                "request_count": 50,
                "error_rate": 2,
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_08_unapproved_simulation_blocked(self):
        response = self.client.post(
            "/api/incidents/TEST-UNAPPROVED/remediation/simulate",
            json={},
        )

        self.assertEqual(response.status_code, 403)

        with self.TestSession() as db:
            workflow = db.get(
                RemediationWorkflow,
                "TEST-UNAPPROVED",
            )

        self.assertIsNone(workflow)

    def test_09_rejected_workflow(self):
        response = self.client.post(
            "/api/incidents/TEST-REJECT/approval",
            json={
                "decision": "REJECT",
                "reviewer": "Integration Tester",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        self.assertEqual(
            response.json()["approval_status"],
            "REJECTED",
        )

        simulate = self.client.post(
            "/api/incidents/TEST-REJECT/remediation/simulate",
            json={},
        )

        self.assertEqual(simulate.status_code, 403)

        with self.TestSession() as db:
            audit = (
                db.query(WorkflowAuditEvent)
                .filter(
                    WorkflowAuditEvent.incident_id ==
                    "TEST-REJECT"
                )
                .all()
            )

        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0].action, "REJECTED")

    def test_10_approved_simulation_and_audit(self):
        approval = self.client.post(
            "/api/incidents/TEST-APPROVE/approval",
            json={
                "decision": "APPROVE",
                "reviewer": "Integration Tester",
            },
        )

        self.assertEqual(
            approval.status_code,
            200,
            approval.text,
        )

        self.assertEqual(
            approval.json()["approval_status"],
            "APPROVED",
        )

        simulation = self.client.post(
            "/api/incidents/TEST-APPROVE/remediation/simulate",
            json={},
        )

        self.assertEqual(
            simulation.status_code,
            200,
            simulation.text,
        )

        self.assertEqual(
            simulation.json()["remediation_status"],
            "SIMULATED",
        )

        workflow = self.client.get(
            "/api/incidents/TEST-APPROVE/workflow"
        )

        self.assertEqual(workflow.status_code, 200)

        actions = [
            event["action"]
            for event in workflow.json()["audit"]
        ]

        self.assertEqual(
            actions,
            ["APPROVED", "REMEDIATION_SIMULATED"],
        )

    def test_11_repeat_simulation_blocked(self):
        # Independent setup in case this test is run alone.
        with self.TestSession() as db:
            workflow = db.get(
                RemediationWorkflow,
                "TEST-APPROVE",
            )

            if workflow is None:
                workflow = RemediationWorkflow(
                    incident_id="TEST-APPROVE",
                    approval_status="APPROVED",
                    remediation_status="SIMULATED",
                    reviewer="Integration Tester",
                    decision_at=datetime.utcnow(),
                    simulation_result="Test simulation only",
                )
                db.add(workflow)
            else:
                workflow.approval_status = "APPROVED"
                workflow.remediation_status = "SIMULATED"

            db.commit()

        response = self.client.post(
            "/api/incidents/TEST-APPROVE/remediation/simulate",
            json={},
        )

        self.assertEqual(response.status_code, 409)

    def test_12_ai_investigation_persistence(self):
        response = self.client.post(
            "/api/incidents/TEST-INVESTIGATE/investigate",
            json={"mode": "DETERMINISTIC"},
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        data = response.json()

        self.assertEqual(
            data["status"],
            "INVESTIGATION_COMPLETED",
        )

        report = data["report"]

        self.assertIn("root_cause", report)
        self.assertIn("confidence", report)
        self.assertTrue(report["findings"])
        self.assertTrue(report["recommendations"])

        saved = self.client.get(
            "/api/incidents/TEST-INVESTIGATE/investigation-report"
        )

        self.assertEqual(saved.status_code, 200)
        self.assertEqual(
            saved.json()["status"],
            "AVAILABLE",
        )

        with self.TestSession() as db:
            incident = db.get(
                Incident,
                "TEST-INVESTIGATE",
            )

            reports = (
                db.query(Evidence)
                .filter(
                    Evidence.incident_id ==
                    "TEST-INVESTIGATE",
                    Evidence.evidence_type ==
                    "AI_INVESTIGATION_REPORT",
                )
                .count()
            )

        self.assertEqual(reports, 1)
        self.assertIsNotNone(incident.root_cause)
        self.assertIsNotNone(incident.confidence)


if __name__ == "__main__":
    unittest.main(verbosity=2)

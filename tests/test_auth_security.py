
"""
NEXUS AI - Phase 9C Authentication Tests

No modifications to the real database.
No production password is printed.

Run:
python -m unittest discover -s tests -p "test_auth_security.py" -v
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import auth as auth_module


TEST_PASSWORD = "Test-Password-Only-123456"

TRUSTED_ORIGIN = {
    "Origin": "http://127.0.0.1:5173"
}

UNTRUSTED_ORIGIN = {
    "Origin": "https://untrusted.example"
}


class TestAuthenticationSecurity(unittest.TestCase):

    def setUp(self):
        # Override authentication settings for this test only.
        # Does not modify the .env file.
        self.environment = patch.dict(
            "os.environ",
            {
                "NEXUS_AUTH_ENABLED": "true",
                "NEXUS_ADMIN_PASSWORD": TEST_PASSWORD,
            },
        )
        self.environment.start()

        # Keep tests independent of prior login failures.
        with auth_module._attempts_lock:
            auth_module._failed_attempts.clear()

        # No app lifespan: avoids database startup changes.
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

        with auth_module._attempts_lock:
            auth_module._failed_attempts.clear()

        self.environment.stop()

    def login(self, password=TEST_PASSWORD):
        return self.client.post(
            "/api/auth/login",
            json={"password": password},
            headers=TRUSTED_ORIGIN,
        )

    def test_01_unauthorized_incidents_blocked(self):
        response = self.client.get("/api/incidents")

        self.assertEqual(response.status_code, 401)

    def test_02_session_initially_unauthenticated(self):
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["auth_enabled"])
        self.assertFalse(data["authenticated"])

    def test_03_invalid_password_rejected(self):
        response = self.login("IncorrectPassword123")

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            response.json()["detail"],
            "Invalid admin password.",
        )

    def test_04_valid_password_accepted(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["status"],
            "LOGIN_SUCCESS",
        )

    def test_05_authenticated_session(self):
        self.assertEqual(self.login().status_code, 200)

        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["role"], "admin")

    def test_06_logout_revokes_browser_session(self):
        self.assertEqual(self.login().status_code, 200)

        response = self.client.post(
            "/api/auth/logout",
            headers=TRUSTED_ORIGIN,
        )

        self.assertEqual(response.status_code, 200)

        state = self.client.get("/api/auth/me")

        self.assertFalse(state.json()["authenticated"])

        protected = self.client.get("/api/incidents")

        self.assertEqual(protected.status_code, 401)

    def test_07_untrusted_login_origin_blocked(self):
        response = self.client.post(
            "/api/auth/login",
            json={"password": TEST_PASSWORD},
            headers=UNTRUSTED_ORIGIN,
        )

        self.assertEqual(response.status_code, 403)

    def test_08_missing_login_origin_blocked(self):
        response = self.client.post(
            "/api/auth/login",
            json={"password": TEST_PASSWORD},
        )

        self.assertEqual(response.status_code, 403)

    def test_09_rate_limit_after_five_failures(self):
        for attempt in range(5):
            response = self.login("IncorrectPassword123")

            self.assertEqual(
                response.status_code,
                401,
                f"Unexpected response on attempt {attempt + 1}",
            )

        # Even the correct password is temporarily locked.
        blocked = self.login(TEST_PASSWORD)

        self.assertEqual(blocked.status_code, 429)

        self.assertIn(
            "Retry-After",
            blocked.headers,
        )

    def test_10_successful_login_clears_failures(self):
        for _ in range(2):
            self.assertEqual(
                self.login("IncorrectPassword123").status_code,
                401,
            )

        self.assertEqual(self.login().status_code, 200)

        self.assertEqual(
            self.login("IncorrectPassword123").status_code,
            401,
        )

        self.assertEqual(
            self.login(TEST_PASSWORD).status_code,
            200,
        )

    def test_11_authenticated_write_rejects_bad_origin(self):
        self.assertEqual(self.login().status_code, 200)

        # A write endpoint with no database mutation:
        # the origin is rejected before endpoint execution.
        response = self.client.post(
            "/api/incidents/TEST-NOT-REAL/approval",
            json={
                "decision": "APPROVE",
                "reviewer": "Security Tester",
            },
            headers=UNTRUSTED_ORIGIN,
        )

        self.assertEqual(response.status_code, 403)

    def test_12_health_remains_public(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()["status"],
            "healthy",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

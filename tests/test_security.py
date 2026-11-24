"""Smoke checks for the security controls of the autoescuela demo app.

Run with: python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Test-only values, set before importing the app so no real secret is needed.
os.environ.setdefault("SECRET_KEY", "local-test-session-key")
os.environ.setdefault("ADMIN_USER", "admin")

from werkzeug.security import generate_password_hash  # noqa: E402

os.environ.setdefault("ADMIN_PASSWORD_HASH", generate_password_hash("local-test-password"))

from app import app  # noqa: E402


class SecuritySmokeTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    @staticmethod
    def token(client):
        with client.session_transaction() as session:
            session["csrf_token"] = "test-csrf-token"
        return "test-csrf-token"

    def test_home_has_security_headers(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        for header, expected in {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
        }.items():
            self.assertEqual(response.headers.get(header), expected)
        self.assertIn("default-src 'self'", response.headers.get("Content-Security-Policy", ""))

    def test_post_without_csrf_is_rejected(self):
        response = self.client.post("/", data={"nombre": "Ana", "telefono": "600123456"})
        self.assertEqual(response.status_code, 400)

    def test_post_with_csrf_is_accepted(self):
        token = self.token(self.client)
        response = self.client.post(
            "/",
            data={"csrf_token": token, "nombre": "Ana", "telefono": "600123456"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/gracias", response.headers["Location"])

    def test_admin_area_requires_session(self):
        response = self.client.get("/autoescuela")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_invalid_login_is_rejected(self):
        token = self.token(self.client)
        response = self.client.post(
            "/login",
            data={
                "csrf_token": token,
                "usuario": "admin",
                "contraseña": "wrong-password",
            },
            environ_base={"REMOTE_ADDR": "127.0.0.42"},
        )
        self.assertEqual(response.status_code, 401)

    def test_logout_is_post_only(self):
        self.assertEqual(self.client.get("/logout").status_code, 405)


if __name__ == "__main__":
    unittest.main()

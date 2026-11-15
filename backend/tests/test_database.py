import os
from pathlib import Path
import subprocess
import sys
import unittest


BACKEND = Path(__file__).resolve().parents[1]


class DatabaseSetupTests(unittest.TestCase):
    def run_python(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {
            key: value
            for key, value in os.environ.items()
            if key.lower() not in {"database_url", "verify_token"}
        }
        env.update(
            DATABASE_URL="postgresql+psycopg2://test:test@localhost/test",
            VERIFY_TOKEN="test",
        )
        result = subprocess.run(
            [sys.executable, *args],
            cwd=BACKEND,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_startup_does_not_connect_or_create_tables(self) -> None:
        self.run_python(
            "-c",
            """
from unittest.mock import patch
from sqlalchemy import MetaData
from sqlalchemy.engine import Engine

with patch.object(Engine, "connect", side_effect=AssertionError("DB connection")), \
     patch.object(MetaData, "create_all", side_effect=AssertionError("Schema creation")):
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello from backend!"}
""",
        )

    def test_migration_generates_postgresql_schema_offline(self) -> None:
        result = self.run_python("-m", "alembic", "upgrade", "head", "--sql")
        self.assertIn("CREATE TABLE messages", result.stdout)
        self.assertIn("attachments JSONB", result.stdout)
        self.assertIn("UNIQUE (mid)", result.stdout)

    def test_request_session_closes_after_failure(self) -> None:
        self.run_python(
            "-c",
            """
from unittest.mock import patch
from database.database import get_db

with patch("database.database.SessionLocal") as factory:
    dependency = get_db()
    assert next(dependency) is factory.return_value
    try:
        dependency.throw(RuntimeError("request failed"))
    except RuntimeError as exc:
        assert str(exc) == "request failed"
    else:
        raise AssertionError("Request error was swallowed")
    factory.return_value.close.assert_called_once_with()
""",
        )


if __name__ == "__main__":
    unittest.main()

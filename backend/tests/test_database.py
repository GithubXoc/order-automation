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

    def test_webhook_database_work_runs_off_event_loop(self) -> None:
        self.run_python(
            "-c",
            """
from threading import get_ident
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from database.database import get_db
from main import app

session = MagicMock()
loop_threads = []
database_threads = []

async def request_session():
    loop_threads.append(get_ident())
    return session

def execute(statement):
    database_threads.append(get_ident())
    return MagicMock()

session.scalars.side_effect = execute
session.commit.side_effect = lambda: database_threads.append(get_ident())
app.dependency_overrides[get_db] = request_session
try:
    with TestClient(app) as client:
        response = client.post("/webhook/", json={"entry": [{"messaging": [{
            "sender": {"id": "customer"},
            "message": {"mid": "one", "text": "hello"},
        }]}]})
    assert response.status_code == 200, response.text
    assert response.text == "Webhook received"
    assert len(loop_threads) == 1
    assert len(database_threads) == 2
    assert all(thread != loop_threads[0] for thread in database_threads), (
        "Synchronous database work ran on the event loop"
    )
finally:
    app.dependency_overrides.clear()
""",
        )

    def test_webhook_saves_every_message_in_batch(self) -> None:
        self.run_python(
            "-c",
            """
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from database.database import get_db
from main import app

def event(mid, timestamp):
    return {
        "sender": {"id": "customer-" + mid},
        "recipient": {"id": "page"},
        "timestamp": timestamp,
        "message": {"mid": mid, "text": "text-" + mid},
    }

session = MagicMock()
app.dependency_overrides[get_db] = lambda: session
payload = {"entry": [
    {"messaging": [event("one", 1), event("two", 2)]},
    {"messaging": [event("three", 3)]},
]}
try:
    with TestClient(app) as client:
        response = client.post("/webhook/", json=payload)
    assert response.status_code == 200, response.text
    messages = [call.args[0].compile().params for call in session.scalars.call_args_list]
    assert [(m["mid"], m["psid"], m["text"]) for m in messages] == [
        ("one", "customer-one", "text-one"),
        ("two", "customer-two", "text-two"),
        ("three", "customer-three", "text-three"),
    ]
    assert session.commit.call_count == 3
finally:
    app.dependency_overrides.clear()
""",
        )


if __name__ == "__main__":
    unittest.main()

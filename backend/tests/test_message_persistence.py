import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "TEST_DATABASE_URL is not set")
class MessagePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        from database.database import get_db
        from main import app
        from models.messages import Messages

        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        self.addCleanup(engine.dispose)
        connection = engine.connect()
        self.addCleanup(connection.close)
        transaction = connection.begin()
        self.addCleanup(transaction.rollback)
        connection.execute(text(
            "CREATE TEMPORARY TABLE messages "
            "(LIKE messages INCLUDING ALL) ON COMMIT DROP"
        ))
        self.session = Session(bind=connection, join_transaction_mode="create_savepoint")
        self.addCleanup(self.session.close)
        self.messages = Messages
        self.enterContext(patch.dict(app.dependency_overrides, {get_db: lambda: self.session}))
        self.client = self.enterContext(TestClient(app))

    def payload(self, *mids: str | None, message_text: str = "original") -> dict:
        return {"entry": [{"messaging": [
            {
                "sender": {"id": "customer"},
                "message": {"mid": mid, "text": message_text},
            }
            for mid in mids
        ]}]}

    def test_retries_and_batch_duplicates_do_not_overwrite_messages(self) -> None:
        response = self.client.post("/webhook/", json=self.payload("one", "one", "two"))
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post(
            "/webhook/", json=self.payload("one", "two", message_text="changed")
        )
        self.assertEqual(response.status_code, 200, response.text)
        messages = self.session.scalars(select(self.messages).order_by(self.messages.mid)).all()
        self.assertEqual([(m.mid, m.text) for m in messages], [
            ("one", "original"), ("two", "original"),
        ])
        self.assertTrue(all(m.id and m.status == "pending" and m.received_at for m in messages))

    def test_missing_message_ids_are_not_deduplicated(self) -> None:
        response = self.client.post("/webhook/", json=self.payload(None, None))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(self.session.scalars(select(self.messages)).all()), 2)

    def test_other_constraint_failures_return_server_error_and_roll_back(self) -> None:
        payload = self.payload("invalid")
        payload["entry"][0]["messaging"][0]["sender"]["id"] = None
        with self.assertLogs("routers.webhook", level="ERROR"):
            response = self.client.post("/webhook/", json=payload)
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Failed to save webhook messages"})
        self.assertEqual(self.session.scalars(select(self.messages)).all(), [])
        response = self.client.post("/webhook/", json=self.payload("valid"))
        self.assertEqual(response.status_code, 200, response.text)


if __name__ == "__main__":
    unittest.main()

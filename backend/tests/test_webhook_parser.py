import unittest

from utils.webhook_parser import parse_events


class WebhookParserTests(unittest.TestCase):
    def test_skipped_events_do_not_hide_later_messages(self) -> None:
        payload = {
            "entry": [
                {"messaging": []},
                {
                    "messaging": [
                        {"message": {"mid": "echo", "is_echo": True}},
                        {"delivery": {"mids": ["delivered"]}},
                        {
                            "sender": {"id": "customer"},
                            "timestamp": 123,
                            "message": {
                                "mid": "message",
                                "text": "hello",
                                "attachments": [
                                    {"type": "image", "payload": {"url": "https://example.com/image"}}
                                ],
                            },
                        },
                    ]
                },
            ]
        }

        events = parse_events(payload)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].mid, "message")
        self.assertEqual(events[0].psid, "customer")
        self.assertEqual(events[0].text, "hello")
        self.assertEqual(events[0].timestamp, 123)
        self.assertEqual(
            events[0].attachments,
            [{"type": "image", "url": "https://example.com/image"}],
        )
        self.assertEqual(events[0].raw, payload)


if __name__ == "__main__":
    unittest.main()

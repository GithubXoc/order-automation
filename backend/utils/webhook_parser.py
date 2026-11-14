from dataclasses import dataclass, field

@dataclass
class IncomingWebhookEvent:
    kind: str # echo or message
    psid: str # always the customer's PSID
    mid: str | None = None
    text: str | None = None
    attachments: list[dict] = field(default_factory=list)
    sticker: bool = False
    reply_to_mid: str | None = None
    quick_reply: str | None = None
    timestamp: int | None = None
    raw: dict = field(default_factory=dict)

def parse_event(event: dict) -> IncomingWebhookEvent | None:
    msg = event.get("message")
    if not isinstance(msg, dict):
        msg = {}

    if not msg:
        return None

    is_echo = msg.get("is_echo", False)

    if is_echo:
        return None

    psid = event["recipient"]["id"] if is_echo else event["sender"]["id"]

    return IncomingWebhookEvent(
        kind="echo" if is_echo else "message",
        psid=psid,
        mid=msg.get("mid"),
        text=msg.get("text"),
        attachments=[
            {"type": a.get("type"), "url": (a.get("payload") or {}).get("url")}
            for a in msg.get("attachments", [])
        ],
        sticker="sticker_id" in msg,
        reply_to_mid=(msg.get("reply_to") or {}).get("mid"),
        quick_reply=(msg.get("quick_reply") or {}).get("payload"),
        timestamp=event.get("timestamp"),
        raw=event,
    )
import uuid
from datetime import datetime
from core.config import settings

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import validates
from database.base_metadata import Base
from sqlalchemy.dialects.postgresql import JSONB

from enum import Enum

class Statuses(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    ANSWERED = "answered"
    SENT = "sent"

class Sender(str, Enum):
    CUSTOMER = "customer"
    PAGE = "page"
    BOT = "bot"


class Messages(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mid = Column(String, unique=True)
    psid = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    text = Column(String)
    attachments = Column(JSONB, default=dict)
    status = Column(String, default=Statuses.PENDING.value)
    answer = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(settings.tz))
    answered_at = Column(DateTime(timezone=True), nullable=True)
    raw = Column(JSONB)

    @validates("sender")
    def validate_sender(self, key, value):
        if value not in {sender.value for sender in Sender}:
            raise ValueError(f"Invalid sender: {value}")
        return value

    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs)
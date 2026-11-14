import uuid
from datetime import datetime
from config import config

from sqlmodel import Field, SQLModel

from enum import Enum

class Statuses(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    ANSWERED = "answered"
    SENT = "sent"


class Messages(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    message: str
    status: Statuses = Field(default=Statuses.PENDING)
    answer: str | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(config.tz))
    answered_at: datetime | None = Field(default=None)
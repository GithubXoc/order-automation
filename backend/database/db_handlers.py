from database.database import SessionDep
from models.messages import Messages, Sender
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from utils.webhook_parser import IncomingWebhookEvent


def create_message(
    session: Session, parsed_event: IncomingWebhookEvent
) -> Messages | None:
    statement = (
        insert(Messages)
        .values(
            mid=parsed_event.mid,
            psid=parsed_event.psid,
            sender=Sender.CUSTOMER.value,
            kind=parsed_event.kind,
            text=parsed_event.text,
            attachments=parsed_event.attachments,
        )
        .on_conflict_do_nothing(index_elements=[Messages.mid])
        .returning(Messages)
    )
    try:
        message = session.scalars(statement).one_or_none()
        session.commit()
        return message

    except SQLAlchemyError:
        session.rollback()
        raise

def get_all_messages(session: SessionDep):
    try:
        return session.query(Messages).all()
    except Exception as exc:
        raise exc


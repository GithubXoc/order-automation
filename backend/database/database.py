from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine, select

from models.messages import Messages


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False is required for SQLite with FastAPI
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

def post_message(session: Session, message: str):
    db_message = Messages(message=message)
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message

def get_messages(session: Session):
    return session.exec(select(Messages)).all()


SessionDep = Annotated[Session, Depends(get_session)]
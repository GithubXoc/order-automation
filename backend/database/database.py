from core.config import settings
from typing import Annotated, Any
from fastapi import Depends
# from sqlmodel import Session, SQLModel, select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

### POSTGRESQL
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
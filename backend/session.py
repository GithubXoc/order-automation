from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

if settings.database_url:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )
    SessionLocal = scoped_session(
        sessionmaker(autocommit=False,autoflush=False,bind=engine)
    )

    if settings.ENVIRONMENT == "development":
        db_info = f"Using database at {settings.database_url}"
        print(db_info)
else:
    raise ValueError("SQLALCHEMY_DATABASE_URI is not set")
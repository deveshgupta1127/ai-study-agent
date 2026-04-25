from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from backend.config import get_settings

from backend.config import get_settings

settings = get_settings()
print("ACTUAL DB URL USED:", settings.DATABASE_URL)

settings=get_settings()

engine=create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

SessionLocal=sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session
)

Base=declarative_base()

def get_db()-> Generator[Session, None, None]:
    """
    Provides a database session per request.
    Ensures proper cleanup after request ends.
    """
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

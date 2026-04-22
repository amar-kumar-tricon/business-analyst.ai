"""
app.db.session
==============
SQLAlchemy engine + Session factory. Use the `get_db` dependency in routes
rather than importing `SessionLocal` directly.

Defaults to a SQLite file — override `DATABASE_URL` in `.env` to point at
local Postgres (or any other SQLAlchemy-supported backend).
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a SQLAlchemy Session and closes it afterward.

    Usage:
        from fastapi import Depends
        from app.db.session import get_db

        @router.get("/thing")
        def read(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

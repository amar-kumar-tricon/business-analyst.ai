"""
app.db.base
===========
Single SQLAlchemy Declarative Base shared by every ORM model.

Why a separate file?  So model modules can import `Base` without importing
`session.py` (which depends on settings and would cause circular imports when
Alembic autogenerates migrations).
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base — inherit from this in every model."""

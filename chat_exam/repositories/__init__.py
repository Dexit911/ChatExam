"""
repositories/__init__.py

Base repository utilities for interacting with SQLAlchemy models.

Provides generic CRUD operations (save, delete, get_by_id, get_by, filter_by)
that can be reused across all repositories in the application.
"""

from typing import TypeVar, Optional, List
from chat_exam.extensions import db

# Generic type variable bound to SQLAlchemy models
M = TypeVar("M", bound=db.Model)


def save(db_obj: M, auto_commit: bool = True) -> M:
    """Add and commit any SQLAlchemy model instance"""
    db.session.add(db_obj)
    if auto_commit: db.session.commit()
    return db_obj

def flush() -> None:
    """Create primary key for object"""
    db.session.flush()

def add(db_obj: M) -> None:
    """Create and commit any SQLAlchemy model instance"""
    db.session.add(db_obj)

def commit(db_obj: M) -> None:
    """Create and commit any SQLAlchemy model instance"""
    db.session.commit(db_obj)

def delete(db_obj: M, auto_commit: bool = True) -> None:
    """Delete any SQLAlchemy model instance"""
    db.session.delete(db_obj)
    if auto_commit: db.session.commit()

def get_by_id(model: db.Model, id_: int) -> Optional[M]:
    """Return a single by primary key (id)"""
    return model.query.get(id_)

def get_by(model: M, **kwargs) -> Optional[M]:
    """Return first single model by **kwargs"""
    return model.query.filter_by(**kwargs).first()

def filter_by(model: M, **kwargs) -> List[M]:
    """Return a list of models by **kwargs"""
    return model.query.filter_by(**kwargs).all()



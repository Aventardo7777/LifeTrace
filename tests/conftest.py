"""Pytest configuration: isolated test database + shared fixtures."""

from __future__ import annotations

import os
import pathlib
import tempfile

# Point the app at an isolated temp database BEFORE importing app modules.
_TMP = pathlib.Path(tempfile.mkdtemp(prefix="lifetrace_test_"))
os.environ["LIFETRACE_DB_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["LIFETRACE_AUTO_SEED"] = "0"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine, init_db
from app.main import app


@pytest.fixture(autouse=True)
def _reset_db():
    """Give every test a clean database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c

from __future__ import annotations

from app.core.config import settings
from pathlib import Path
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db import session as db_session


def _assert_safe_test_database_url(database_url: str, development_database_url: str)->None:
    test_url = make_url(database_url)
    development_url = make_url(development_database_url)
    
    if test_url.render_as_string(hide_password=True) == development_url.render_as_string(hide_password=True):
        raise RuntimeError("TEST_DATABASE_URL must not be the same as DATABASE_URL")
    database_name = test_url.database
    if not database_name:
        raise RuntimeError("TEST_DATABASAE_URL must include a database name")
    if not database_name.endswith("_test"):
        safe_url = test_url.render_as_string(hide_password=True)
        raise RuntimeError(
            f"TEST_DATABASE_URL must point to a database ending with _test : {safe_url}"
        )
        
TEST_DATABASE_URL = settings.test_database_url
DATABASE_URL = settings.database_url

if TEST_DATABASE_URL is None:
    raise RuntimeError("TEST_DATABASE_URL is required for tests")

_assert_safe_test_database_url(TEST_DATABASE_URL, DATABASE_URL)

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if TEST_DATABASE_URL.startswith("sqlite")
    else {},
)

db_session.engine = test_engine
db_session.SessionLocal.configure(bind=test_engine)

def override_get_db()->Generator[Session, None, None]:
    db = db_session.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
import app.models
from app.db.base import Base
from app.main import app

Base.metadata.create_all(bind=test_engine)
app.dependency_overrides[db_session.get_db] = override_get_db

@pytest.fixture
def client()->Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


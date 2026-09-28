from __future__ import annotations

from app.core.config import settings
from pathlib import Path
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db import session as db_session_module


def _assert_safe_test_database_url(database_url: str, development_database_url: str)->None:
    test_url = make_url(database_url)
    development_url = make_url(development_database_url)
    
    if test_url.render_as_string(hide_password=True) == development_url.render_as_string(hide_password=True):
        raise RuntimeError("TEST_DATABASE_URL must not be the same as DATABASE_URL")
    database_name = test_url.database
    if not database_name:
        raise RuntimeError("TEST_DATABASE_URL must include a database name")
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

db_session_module.engine = test_engine
db_session_module.SessionLocal.configure(bind=test_engine)

def override_get_db()->Generator[Session, None, None]:
    db = db_session_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
import app.models
from app.db.base import Base
from app.main import app

Base.metadata.create_all(bind=test_engine)
app.dependency_overrides[db_session_module.get_db] = override_get_db

def _reset_test_database()->None:
    with test_engine.begin() as connection:
        if test_engine.dialect.name == "postgresql":
            table_names = ", ".join(
                f'"{table.name}"' for table in Base.metadata.sorted_tables
            )
            if table_names:
                connection.execute(
                    text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
                )
        else:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())

@pytest.fixture(autouse=True)
def reset_test_database()->Generator[None,None,None]:
    _reset_test_database()
    yield
    _reset_test_database()

@pytest.fixture
def client()->Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
        
@pytest.fixture
def db_session()->Generator[Session, None, None]:
    db = db_session_module.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@pytest.fixture
def auth_headers()->Callable[[int, str], dict[str,str]]:
    def _auth_headers(workspace_id: int, role: str = "admin") -> dict[str,str]:
        return{
            "X-User-Id":"1",
            "X-Workspace-Id":str(workspace_id),
            "X-User-Role":role,
        }
    return _auth_headers

@pytest.fixture(autouse=True)
def disable_process_run_task_delay(monkeypatch)->None:
    monkeypatch.setattr(
        "app.api.routes.runs.process_run_task.delay",
        lambda run_id: None,
    )
from __future__ import annotations

import os 
import shutil
import tempfile
from pathlib import Path
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db import session as db_session

_TEST_DB_DIR: Path | None = None

def _default_test_database_url()->str:
    global _TEST_DB_DIR
    
    _TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="agentops-tests"))
    test_db_path = _TEST_DB_DIR / "agentops_test.db"
    
    return f"sqlite:///{test_db_path.as_posix()}"

def _asssert_safe_test_database_url(database_url: str)->None:
    url = make_url(database_url)
    if url.get_backend_name() == "sqlite" and url.database:
        if Path(url.database).name == "agentops.db":
            raise RuntimeError("Tests must not user development database agentops.db")
        
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or _default_test_database_url()

_asssert_safe_test_database_url(TEST_DATABASE_URL)

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

def pytest_sessionfinish(session, exitstatus)->None:
    test_engine.dispose()
    
    if _TEST_DB_DIR is not None:
        shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)